import time
import statsd


# region StatsDConfiguration Class
class StatsDConfiguration:
    """
    A Class used to hold the statsd exporter configuration.

    Attributes
    ----------
    host: str
        host address where statsd/statsd exporter is running. we are going to keep this as localhost only as we will
        have statsd-exporter install on each server
    port: int
        port number where stats-exporter is running.
    prefix: str
        to distinguish multiple application or env using the same statsd server. It will prepend to all stats. As a
        standard practise, we will be passing project name as the prefix for all our metrics.
    """
    def __init__(self, host, port, prefix):
        """
        Parameters
        ----------
        host: str
            host url of statsd exporter
        port: int
            port of statsd exporter
        prefix: str
            project name from which we want to publish the metrics
        """
        self.__host = host
        self.__port = port
        self.__prefix = prefix

    @property
    def host(self):
        return self.__host

    @property
    def port(self):
        return self.__port

    @property
    def prefix(self):
        return self.__prefix


# endregion


# region StatsDClient class
class StatsDClient:
    """
       Class to provide the statsd client

       Methods
       -------
       instance(config)
            creates the statsd client and provide a singleton instance of it.
       """
    __client = None

    def __init__(self):
        """ There is no use of constructor """
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls, config=None):
        """
        Creates the statsd client using the StatsDConfiguration, and provide a singleton instance of statsd client.
        """
        if cls.__client is None:
            try:
                # TODO: Instead of passing the config argument, we should be defaulting to predefined host, port using
                #  environment file.
                cls.__client = statsd.StatsClient(host=config.host, port=config.port, prefix=config.prefix)
            except Exception as ex:
                print(str(ex))
                cls.__client = None
        return cls.__client


# endregion


# region PromMetricCollector Class
class PrometheusMetricCollector:
    """
    A Wrapper on statsclient to log different type of metrics.

    host: host address where statsd/statsd exporter is running.
    port: statsd/statsd exporter server port.
    prefix: to distinguish multiple application or env using the same statsd server. It will prepend to all stats.
    """

    def __init__(self, stats_config):
        """
        Constructor to initialize PrometheusMetricCollector
        Argument
        --------
        Takes StatsDConfiguration as the argument.
        """
        self.__client = StatsDClient.instance(stats_config)

    def collect_timer_metrics(self, stat, time_delta):
        """
        Collects timing metrics. Make sure to pass value in ms only.
        Parameters
        ----------
        stat: str
            the metrics name, which you want to log. For e.g http_request_count.endpoint.http_method.response_code
            You can append any number of string, prepend with . (dot). In the statsd exporter mapping file make sure
            to match this with $n style references.

        time_delta: float
            the time difference between the event start and completion. Make sure to pass this in ms.
        """
        # IMP: value should be in ms
        self.__client.timing(stat, time_delta)

    def collect_counter_metrics(self, stat, count=1, counter_type='incr'):
        """
        Collects counter metrics.
        Parameters
        ----------
        stat: str
            the metrics name, which you want to log. For e.g http_request_count.endpoint.http_method.response_code
            You can append any number of string, prepend with . (dot). In the statsd exporter mapping file make sure
            to match this with $n style references.
        count: int (optional)
            Counter metrics can be increased or decreased. count parameter will increase or decrease the metrics by that
            factor.
        counter_type: str (optional)
            incr/decr: depending on this flag, counter metrics will increase or decrease the metrics value.

        """
        if counter_type == 'incr':
            self.__client.incr(stat, count)
        else:
            self.__client.decr(stat, count)

    def collect_gauge_metrics(self, stat, value):
        """
        Collects gauge metrics. Gauge are constant data type. they can be used where you don't need to reset it
        periodically. for e.g Number of Client connection.
        Parameters
        ----------
        stat: str
            the metrics name, which you want to log. For e.g http_request_count.endpoint.http_method.response_code
            You can append any number of string, prepend with . (dot). In the statsd exporter mapping file make sure
            to match this with $n style references.
        value: any value that you want to set to gauge metrics.
        """
        self.__client.gauge(stat, value)

    def collect_sets_metrics(self, stat, value):
        """
        Collects sets metrics: Counts the number of unique values passed to a key.
        """
        self.__client.set(stat, value)


# endregion


# region decorators
def django_request_time_decorator(collector):
    """
    Decorator to log metrics related to http request

    Methods
    -------
    wrapper
        wraps the http get & post call and calculate the time taken to process the request.
        also checks the response code of each endpoint and pushes them to statsd exporter.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            path = 'INVALID'
            method = 'INVALID'
            status_code = '503'
            try:
                start_time = time.time()
                request = args[0] if len(args) > 0 else None
                if request:
                    path = request.path
                    method = request.method
                response = func(*args, **kwargs)
                status_code = response.status_code
            except Exception as e:
                collector.collect_timer_metrics('http_request_duration_seconds.{}'.format(path),
                                                (time.time() - start_time) * 1000)
                collector.collect_counter_metrics('http_request_count.{}.{}.{}'.format(path, method, status_code))
                raise e
            collector.collect_timer_metrics('http_request_duration_seconds.{}'.format(path),
                                            (time.time() - start_time) * 1000)
            collector.collect_counter_metrics('http_request_count.{}.{}.{}'.format(path, method, status_code))
            return response

        return wrapper

    return decorator

# endregion

