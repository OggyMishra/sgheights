# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from chunked_upload.views import ChunkedUploadCompleteView, ChunkedUploadView
from django.http import HttpResponse
from rest_framework.decorators import authentication_classes, permission_classes
from django.shortcuts import render

# Create your views here.
#from sgheights.pocapp.models import SgChunkedUpload
from rest_framework.permissions import AllowAny

from .models import SgChunkedUpload


class UserDataWorker(object):
    prom_metrics = 'hello'


class UserDataUploadWorker(UserDataWorker):

    def __init__(self, worker):
        self.worker = worker

    def process_upload_queue(self):
        print(self.prom_metrics)
        print(self.worker)


def index(request):
    r = UserDataUploadWorker(1)
    r.process_upload_queue()
    return HttpResponse('hello pocapp')


def hello_point(request):
    print('hello')
    print('hi')
    return HttpResponse('Hello')


class MyChunkedUploadView(ChunkedUploadView):
    model = SgChunkedUpload
    field_name = 'the_file'

    def check_permissions(self, request):
        # Allow non authenticated users to make uploads
        pass

def hello(request):
    print('hi')



class MyChunkedUploadCompleteView(ChunkedUploadCompleteView):

    model = SgChunkedUpload

    def check_permissions(self, request):
        # Allow non authenticated users to make uploads
        pass

    def on_completion(self, uploaded_file, request):
        request.FILES['attachments[]'] = uploaded_file.file
        post_values = request.POST.copy()
        post_values["hi"] = "hello"
        request.POST = post_values
        hello(request)


        # Do something with the uploaded file. E.g.:
        # * Store the uploaded file on another model:
        # SomeModel.objects.create(user=request.user, file=uploaded_file)
        # * Pass it as an argument to a function:
        # function_that_process_file(uploaded_file)
        pass

    def get_response_data(self, chunked_upload, request):
        chunked_upload
        return {'message': ("You successfully uploaded '%s' (%s bytes)!" %
                            (chunked_upload.filename, chunked_upload.offset))}