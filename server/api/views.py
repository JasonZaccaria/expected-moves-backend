from distutils.log import error
from email import header
import json
from xmlrpc.client import ResponseError
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import TaskSerializer
from utils import expected_move, quotes
# Create your views here.
from .models import Task
import time
import random


class main(APIView):
    
    def __init__(self):

        self.ticker = ''

    def post(self, request):

        try:
            self.ticker = self.request.POST.get('text')   
            self.stdv = self.request.POST.get('radio')
            self.dict_test = {'ticker':self.ticker, 'radioType':self.stdv}
            self.data_instance = expected_move.OPTIONS_PROBABILITY_CONE(self.ticker,self.stdv)
            self.expected_move_data = self.data_instance.graph()
            self.quotes_data = self.data_instance.quotes()
            print(self.expected_move_data)
            print(self.quotes_data)
            self.return_data = {'expected_moves':self.expected_move_data, 'quotes':self.quotes_data}
            self.request.session['text'] = self.ticker
            self.request.session.save()
            return Response(self.return_data)

        except:

            self.test = self.request.session['text']
            self.error = {'error':self.test}
            return Response(error('not valid ticker'), status=400, exception=True)

    def get(self, request):
        
        print(self.request.session['text'])
        self.ticker = self.request.session.get('text')
        self.quotes_data = quotes.Quotes(self.ticker)
        self.object = self.quotes_data.get_data()
        self.returner = {'quotes': self.object}
        return Response(self.returner)