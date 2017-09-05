from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.views import generic
from django.core import serializers
from django.db.models import Avg, When, Sum, Case, FloatField

from datetime import datetime, date, timedelta
import pytz
import json
import pandas as pd

from .models import ASN, Country, Delay, Forwarding, Delay_alarms, Forwarding_alarms, Disco_events, Disco_probes

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import filters, generics
from .serializers import DelaySerializer, ForwardingSerializer, DelayAlarmsSerializer, ForwardingAlarmsSerializer, DiscoEventsSerializer, DiscoProbesSerializer


class DelayView(generics.ListAPIView): #viewsets.ModelViewSet):
    """
    API endpoint that allows to view the level of congestion.
    """
    queryset = Delay.objects.all() #.order_by('-asn')
    serializer_class = DelaySerializer
    filter_backends = (filters.DjangoFilterBackend,filters.OrderingFilter,)
    filter_fields = ('asn', 'timebin',  'magnitude', 'deviation', 'label' ) 
    ordering_fields = ('timebin', 'magnitude', 'deviation')


class ForwardingView(generics.ListAPIView):
    """
    API endpoint that allows to view the level of forwarding anomaly.
    """
    queryset = Forwarding.objects.all()
    serializer_class = ForwardingSerializer
    filter_backends = (filters.DjangoFilterBackend,filters.OrderingFilter,)
    filter_fields = ('asn', 'timebin', 'magnitude', 'resp', 'label')
    ordering_fields = ('timebin', 'magnitude', 'deviation')


class DelayAlarmsView(generics.ListAPIView): 
    """
    API endpoint that allows to view the delay alarms.
    """
    queryset = Delay_alarms.objects.all() #.order_by('-asn')
    serializer_class = DelayAlarmsSerializer
    filter_backends = (filters.DjangoFilterBackend,filters.OrderingFilter,)
    filter_fields = ('asn', 'timebin',  'link', 'deviation', 'nbprobes' ) 
    ordering_fields = ('timebin', 'deviation', 'nbprobes', 'diffmedian', 'medianrtt')


class ForwardingAlarmsView(generics.ListAPIView):
    """
    API endpoint that allows to view the forwarding alarms.
    """
    queryset = Forwarding_alarms.objects.all()
    serializer_class = ForwardingAlarmsSerializer
    filter_backends = (filters.DjangoFilterBackend,filters.OrderingFilter,)
    filter_fields = ('asn', 'timebin', 'ip', 'previoushop', 'correlation', 'responsibility')
    ordering_fields = ('timebin', 'correlation', 'responsibility')

class DiscoEventsView(generics.ListAPIView):
    """
    API endpoint that allows to view the events reported by disco.
    """
    queryset = Disco_events.objects.all()
    serializer_class = DiscoEventsSerializer
    filter_backends = (filters.DjangoFilterBackend,filters.OrderingFilter,)
    filter_fields = ('streamtype', 'streamname', 'starttime', 'endtime', 'avglevel', 'nbdiscoprobes', 'totalprobes', 'ongoing')
    ordering_fields = ('starttime', 'endtime', 'avglevel', 'nbdiscoprobes')


class DiscoProbesView(generics.ListAPIView): 
    """
    API endpoint that allows to view disconnected probes.
    """
    queryset = Disco_probes.objects.all() #.order_by('-asn')
    serializer_class = DiscoProbesSerializer
    filter_backends = (filters.DjangoFilterBackend,filters.OrderingFilter,)
    filter_fields = ('probe_id', 'event',  'starttime', 'endtime', 'level' ) 
    ordering_fields = ('starttime', 'endtime', 'level')



@api_view(['GET'])
def restful_API(request, format=None):
    """
    API endpoint
    """
    return Response({
        'forwarding': reverse('ihr:forwardingListView', request=request, format=format),
        'delay': reverse('ihr:delayListView', request=request, format=format),
        'forwarding_alarms': reverse('ihr:forwardingAlarmsListView', request=request, format=format),
        'delay_alarms': reverse('ihr:delayAlarmsListView', request=request, format=format),
        'disco_events': reverse('ihr:discoEventsListView', request=request, format=format),
        'disco_probes': reverse('ihr:discoProbesListView', request=request, format=format),
    })

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            # return o.isoformat()
            return o.strftime("%Y-%m-%d %H:%M:%S")

        return json.JSONEncoder.default(self, o)

def index_old(request):

    # Top congested ASs
    # today = date.today()
    # if "today" in request.GET:
        # part = request.GET["today"].split("-")
        # today = date(int(part[0]), int(part[1]), int(part[2]))
    # limitDate = today-timedelta(days=7)
    # print(limitDate)
    # # TODO remove the following line (used only with test data)
    # limitDate = datetime(2015,1,1)

    # topCongestion = ASN.objects.filter(congestion__timebin__gt=limitDate).annotate(score=Sum("congestion__magnitude")).order_by("-score")[:5]

    # tier1 = ASN.objects.filter(number__in = [7018,174,209,3320,3257,286,3356,3549,2914,5511,1239,6453,6762,12956,1299,701,702,703,2828,6461])
    topTier1 = ASN.objects.filter(number__in = [3356, 174, 3257, 1299, 2914])
    rootServers = ASN.objects.filter(number__in = [26415, 2149, 27, 297, 3557, 5927, 13, 29216, 26415, 25152, 20144, 7500, 226])
    monitoredAsn = ASN.objects.order_by("number")

    ulLen = 5
    if len(monitoredAsn)<15:
        ulLen = 2 #len(monitoredAsn)/3
    
    date = ""
    if "date" in request.GET:
        date = request.GET["date"]

    last = 30
    if "last" in request.GET:
        last = request.GET["last"]

    context = {"monitoredAsn0": monitoredAsn[1:ulLen+1], "monitoredAsn1": monitoredAsn[ulLen+1:1+ulLen*2],
            "monitoredAsn2": monitoredAsn[1+ulLen*2:1+ulLen*3],"monitoredAsn3": monitoredAsn[1+ulLen*3:1+ulLen*4],
            "nbMonitoredAsn": len(monitoredAsn)-ulLen*4,
            "topTier1": topTier1 ,
            "rootServers": rootServers ,
            "date": date,
            "last": last,
            }
    return render(request, "ihr/index.html", context)

def index(request):

    # Top congested ASs
    # today = date.today()
    # if "today" in request.GET:
        # part = request.GET["today"].split("-")
        # today = date(int(part[0]), int(part[1]), int(part[2]))
    # limitDate = today-timedelta(days=7)

    # topCongestion = ASN.objects.filter(congestion__timebin__gt=limitDate).annotate(score=Sum("congestion__magnitude")).order_by("-score")[:5]

    # format the end date
    dtEnd = datetime.now(pytz.utc)
    if "date" in request.GET and request.GET["date"].count("-") == 2:
        date = request.GET["date"].split("-")
        dtEnd = datetime(int(date[0]), int(date[1]), int(date[2]), tzinfo=pytz.utc) 

    # set the data duration
    last = 30
    if "last" in request.GET:
        last = int(request.GET["last"])
        if last > 356:
            last = 356

    dtStart = dtEnd - timedelta(last)

    # tier1 = ASN.objects.filter(number__in = [7018,174,209,3320,3257,286,3356,3549,2914,5511,1239,6453,6762,12956,1299,701,702,703,2828,6461])
    topTier1 = ASN.objects.filter(number__in = [3356, 174, 3257, 1299, 2914])
    # rootServers = ASN.objects.filter(number__in = [26415, 2149, 27, 297, 3557, 
        # 5927, 13, 29216, 26415, 25152, 20144, 7500, 226])
    monitoredAsn = ASN.objects.filter(number__in = [15169, 20940, 7018,209,3320,
        286,3549,5511,1239,6453,6762,12956,701,702,703,2828,6461])
    monitoredCountry = Country.objects.filter(code__in = ["NL","FR","US","IR",
        "ES","DE","JP", "CH", "GB", "IT", "BE", "UA", "PL", "CZ", "CA", "RU", 
        "BG","SE","AT","DK","AU","FI","GR","IE","NO","NZ","ZA"])
    nbAsn = ASN.objects.count()
    nbCountry = Country.objects.count()

    ulLen = monitoredAsn.count()/2
    ulLen2 = monitoredCountry.count()/2
    
    date = ""
    if "date" in request.GET:
        date = request.GET["date"]

    last = 30
    if "last" in request.GET:
        last = request.GET["last"]

    context = {
            "nbMonitoredAsn": nbAsn-monitoredAsn.count(),
            "nbMonitoredCountry": nbCountry-monitoredCountry.count(),
            "monitoredAsn": monitoredAsn,
            "monitoredCountry": monitoredCountry,
            "topTier1": topTier1 ,
            # "rootServers": rootServers ,
            "date": date,
            "last": last,
            }
    return render(request, "ihr/index.html", context)

def search(request):
    req = request.GET["asn"]
    reqNumber = -1 
    try:
        if req.startswith("asn"):
            reqNumber = int(req[3:].partition(" ")[0]) 
        elif req.startswith("as"):
            reqNumber = int(req[2:].partition(" ")[0]) 
        else:
            reqNumber = int(req.partition(" ")[0])
    except ValueError:
        return HttpResponseRedirect(reverse("ihr:index"))
    
    asn = get_object_or_404(ASN, number=reqNumber)
    return HttpResponseRedirect(reverse("ihr:asnDetail", args=(asn.number,)))

def delayData(request):
    asn = get_object_or_404(ASN, number=request.GET["asn"])

    dtEnd = datetime.now(pytz.utc)
    if "date" in request.GET and request.GET["date"].count("-") == 2:
        date = request.GET["date"].split("-")
        dtEnd = datetime(int(date[0]), int(date[1]), int(date[2]),23,59, tzinfo=pytz.utc) 

    last = 30 
    if "last" in request.GET:
        last = int(request.GET["last"])
        if last > 356:
            last = 356

    dtStart = dtEnd - timedelta(last)

    data = Delay.objects.filter(asn=asn.number, timebin__gte=dtStart,  timebin__lte=dtEnd).order_by("timebin")
    formatedData = {"AS"+str(asn.number): {
            "x": list(data.values_list("timebin", flat=True)),
            "y": list(data.values_list("magnitude", flat=True))
            }}
    return JsonResponse(formatedData, encoder=DateTimeEncoder) 

def forwardingData(request):
    asn = get_object_or_404(ASN, number=request.GET["asn"])

    dtEnd = datetime.now(pytz.utc)
    if "date" in request.GET and request.GET["date"].count("-") == 2:
        date = request.GET["date"].split("-")
        dtEnd = datetime(int(date[0]), int(date[1]), int(date[2]),23,59, tzinfo=pytz.utc) 

    last = 30
    if "last" in request.GET:
        last = int(request.GET["last"])
        if last > 356:
            last = 356

    dtStart = dtEnd - timedelta(last)

    data = Forwarding.objects.filter(asn=asn.number, timebin__gte=dtStart,  timebin__lte=dtEnd).order_by("timebin") 
    formatedData ={"AS"+str(asn.number): {
            "x": list(data.values_list("timebin", flat=True)),
            "y": list(data.values_list("magnitude", flat=True))
            }}
    return JsonResponse(formatedData, encoder=DateTimeEncoder) 


def eventToStepGraph(dtStart, dtEnd, stime, etime, lvl, eventid):
    """Convert a disco event to a list of x, y ,eventid values for the step
    graph.
    """

    x = [dtStart]
    y = ["0"]
    ei = ["0"]

    # change the first value if there is an event starting before dtStart
    if len(stime) and min(stime) < dtStart:
        idx = stime.index(min(stime))
        y[0] = lvl[idx]
        ei[0] = eventid[idx]
        x.append(etime[idx])
        x.append(etime[idx])
        y.append(y[0])
        y.append("0")
        ei.append(ei[0])
        ei.append("0")

        stime.pop(idx) 
        etime.pop(idx)
        lvl.pop(idx)
        eventid.pop(idx)

    for s, e, l, i in zip(stime,etime,lvl,eventid):
        x.append(s)
        x.append(s)
        x.append(e)
        x.append(e)
        y.append("0")
        y.append(l)
        y.append(l)
        y.append("0")
        ei.append("0")
        ei.append(i)
        ei.append(i)
        ei.append("0")
    
    if x[-1] < dtEnd:
        x.append(dtEnd)
        y.append("0")
        ei.append("0")

    return x, y, ei


def discoData(request):
    # format the end date
    dtEnd = datetime.now(pytz.utc)
    if "date" in request.GET and request.GET["date"].count("-") == 2:
        date = request.GET["date"].split("-")
        dtEnd = datetime(int(date[0]), int(date[1]), int(date[2]), 23, 59, tzinfo=pytz.utc) 

    # set the data duration
    last = 30
    if "last" in request.GET:
        last = int(request.GET["last"])
        if last > 356:
            last = 356

    dtStart = dtEnd - timedelta(last)

    # find corresponding ASN or country
    if "asn" in request.GET:
        asn = get_object_or_404(ASN, number=request.GET["asn"])
        streams= [{"streamtype":"asn", "streamname": asn.number}]
    elif "cc" in request.GET:
        country = get_object_or_404(Country, code=request.GET["cc"])
        streams= [{"streamtype":"country", "streamname": country.code}]
    else:
        streams = Disco_events.objects.filter(endtime__gte=dtStart,
            starttime__lte=dtEnd,avglevel__gte=12).exclude(streamtype="geo").distinct("streamname").values("streamname", "streamtype")
        
    formatedData = {}
    for stream in streams:
        streamtype = stream["streamtype"]
        streamname = stream["streamname"]

        data = Disco_events.objects.filter(streamtype=streamtype, streamname=streamname, 
                endtime__gte=dtStart,  starttime__lte=dtEnd,avglevel__gte=12).order_by("starttime") 
        stime = list(data.values_list("starttime", flat=True))
        etime = list(data.values_list("endtime", flat=True))
        lvl =   list(data.values_list("avglevel", flat=True))
        eventid=list(data.values_list("id", flat=True))

        x, y ,ei = eventToStepGraph(dtStart, dtEnd, stime, etime, lvl, eventid)

        df = pd.DataFrame({"lvl": y, "eid": ei}, index=x)
        prefix = "CC" if streamtype=="country" else "AS"
        formatedData[prefix+str(streamname)] = {
                "streamtype": streamtype,
                "streamname": streamname,
                "dtStart": dtStart,
                "dtEnd": dtEnd,
                "stime": stime,
                "etime": etime,
                "rawx": x,
                "rawy": y,
                "rawe": ei,
                "x": list(df.index.to_pydatetime()),
                "y": list(df["lvl"].values),
                "eventid": list(df["eid"].values),
                }

    return JsonResponse(formatedData, encoder=DateTimeEncoder) 



# def discoData(request):
    # if "asn" in request.GET:
        # streamtype = "asn"
        # asn = get_object_or_404(ASN, number=request.GET["asn"])
        # streamname = asn.number
    # elif "cc" in request.GET:
        # streamtype= "country"
        # country = get_object_or_404(Country, code=request.GET["cc"])
        # streamname = country.code

    # dtEnd = datetime.now(pytz.utc)
    # if "date" in request.GET and request.GET["date"].count("-") == 2:
        # date = request.GET["date"].split("-")
        # dtEnd = datetime(int(date[0]), int(date[1]), int(date[2]), tzinfo=pytz.utc) 

    # last = 30
    # if "last" in request.GET:
        # last = int(request.GET["last"])
        # if last > 356:
            # last = 356

    # dtStart = dtEnd - timedelta(last)

    # data = Disco_events.objects.filter(streamtype=streamtype, streamname=streamname, 
            # endtime__gte=dtStart,  starttime__lte=dtEnd).order_by("starttime") 
    # stime = list(data.values_list("starttime", flat=True))
    # etime = list(data.values_list("endtime", flat=True))
    # lvl =   list(data.values_list("avglevel", flat=True))
    # eventid=list(data.values_list("id", flat=True))
    # x = []
    # y = []
    # ei = []
    # for s, e, l, i in zip(stime,etime,lvl,eventid):
        # x.append(s)
        # x.append(e)
        # y.append(l)
        # y.append(l)
        # ei.append(i)
        # ei.append(i)

    # formatedData = {
            # "x": x,
            # "y": y,
            # "eventid": ei,
            # }
    # return JsonResponse(formatedData, encoder=DateTimeEncoder) 



class ASNDetail(generic.DetailView):
    model = ASN
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ASNDetail, self).get_context_data(**kwargs)

        date = ""
        if "date" in self.request.GET:
            date = self.request.GET["date"]

        last = 30
        if "last" in self.request.GET:
            last = self.request.GET["last"]

        context["date"] = date;
        context["last"] = last;

        return context;

    # template_name = "ihr/asn_detail.html"



class CountryDetail(generic.DetailView):
    model = Country
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CountryDetail, self).get_context_data(**kwargs)

        date = ""
        if "date" in self.request.GET:
            date = self.request.GET["date"]

        last = 30
        if "last" in self.request.GET:
            last = self.request.GET["last"]

        context["date"] = date;
        context["last"] = last;

        return context;



class ASNList(generic.ListView):
    model = ASN
    ordering = ["number"]


class CountryList(generic.ListView):
    model = Country
    ordering = ["name"]


class DiscoDetail(generic.DetailView):
    model = Disco_events
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(DiscoDetail, self).get_context_data(**kwargs)

        return context;

    template_name = "ihr/disco_detail.html"
