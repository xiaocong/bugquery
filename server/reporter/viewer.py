#!/usr/bin/env python

import redis

import string
import json
from pyExcelerator import *
# from bottle import response
import time
from datetime import datetime, date, timedelta

# import urllib2

import uuid

# import proxy

from db import dbHelper
import dcrator
import auth


class Viewer(object):

    '''
    Class mainly for query bug report data
    '''

    def __init__(self):
        self.redis = dbHelper.redisDB
        self.pipe = dbHelper.redisPipe

    # keys list of phone properties
    def info_keys(self):
        return list(self.redis.smembers('i:k'))

    # values list of a specified key of phone property
    def info_values(self, key):
        return list(self.redis.smembers('i:k:%s' % key))

    def platforms(self):
        return self.redis.sort('i:k:android.os.Build.VERSION.RELEASE', alpha=True)

    def info_release_product(self, accessible):
        redis = self.redis
        pipe = self.pipe

        platforms = self.platforms()

        for platform in platforms:
            pipe.smembers('set:%s:product' % platform)
        ret = pipe.execute()

        results = {}
        i = 0
        for platform in platforms:
            l = list(set(accessible) & set(ret[i]))
            if (len(l) > 0):
                results[platform] = l
            i += 1
        return results

    def errorTypes(self):
        return self.redis.sort('b:t', alpha=True)

    def getLatestId(self, imei):
        '''
        return: [1,2,3] or None
        '''
        redis = self.redis
        ret = redis.sort('ids:i:deviceId:%s' % imei, desc=True, start=0, num=3)
        if len(ret) == 0:
            return None
        else:
            return ret

    @dcrator.timeit
    def appList(self):
        # Get all apps in type:ANR,FORCE_CLOSE,CORE_DUMP,SYSTEM_APP_WTF,SYSTEM_APP_STRICTMODE
        # sets = []
        # sets.append('b:t:ANR')
        # sets.append('b:t:FORCE_CLOSE')
        # sets.append('b:t:CORE_DUMP')
        # sets.append('b:t:SYSTEM_APP_WTF')
        # sets.append('b:t:SYSTEM_APP_STRICTMODE')
        # return list(self.redis.sunion(sets))
        return self.redis.sort('set:b:name', alpha=True)

    @dcrator.timeit
    def errors(self, accessible, paging, conditions):
        pagingCached = False
        pagingSet = None
        page = int(paging['page'])
        records = int(paging['records'])  # Not limit the size
        totalRecords = None
        paging_token = None
        if 'paging_token' in paging:
            paging_token = paging['paging_token']
            pagingSet = "tmp_paging_%s" % paging_token
            if self.redis.exists(pagingSet):
                pagingCached = True

        if pagingCached:
            self.pipe.expire(pagingSet, 30 * 60)
            self.pipe.scard(pagingSet)
            self.pipe.sort(
                pagingSet, desc=True, start=(page - 1) * records, num=records)
            result = self.pipe.execute()
            totalRecords = result[1]
            ret = result[2]
        else:
            sets = []
            paging_token = str(uuid.uuid4())
            pagingSet = "tmp_paging_%s" % paging_token

            # processing accessible set
            keyProduct = 'android.os.Build.PRODUCT'
            keyPlatform = 'android.os.Build.VERSION.RELEASE'
            if keyPlatform in conditions and keyProduct in conditions:
                sets.append('ids:%s:%s' %
                            (conditions.pop(keyPlatform), conditions.pop(keyProduct)))
            elif keyProduct in conditions:
                sets.append('ids:i:android.os.Build.PRODUCT:%s' %
                            conditions.pop(keyProduct))
            else:
                accessibleSet = self.getAccessibleSet(accessible)
                if accessibleSet is None:
                    return None
                else:
                    sets.append(accessibleSet)

            # processing time filtered set
            if self.needTimeFilter(conditions):
                timeFilteredSet = self.getTimeFilteredSet(conditions)
                if timeFilteredSet is None:
                    return None
                else:
                    sets.append(timeFilteredSet)

            # processing error type
            if 'e_type' in conditions:
                sets.append('ids:b:%s' % conditions.pop('e_type'))
            else:
                sets.append('ids:b')

            # processing name
            if 'name' in conditions:
                sets.append('ids:b:%s' % conditions.pop('name'))

            # Other system info conditions
            for key in conditions:
                sets.append('ids:i:%s:%s' % (key, conditions[key]))
            print sets
            self.pipe.sinterstore(pagingSet, sets)
            self.pipe.sort(
                pagingSet, desc=True, start=(page - 1) * records, num=records)
            self.pipe.expire(pagingSet, 60 * 30)
            result = self.pipe.execute()
            totalRecords = result[0]
            ret = result[1]
        if len(ret) == 0:
            return None
        else:
            # paging={}
            paging['totalrecords'] = totalRecords
            remainder = totalRecords % records
            if remainder > 0:
                paging['totalpages'] = totalRecords / records + 1
            else:
                paging['totalpages'] = totalRecords / records
            paging['paging_token'] = paging_token
            results = {'paging': paging, 'data': ret}
            return results

    @dcrator.timeit
    def getAccessibleSet(self, accessible):
        '''
        '''
        tmpSet = 'tmp_%s' % str(uuid.uuid4())
        sets = []
        for product in accessible:
            sets.append('ids:i:android.os.Build.PRODUCT:%s' % product)
        self.pipe.sunionstore(tmpSet, sets)
        self.pipe.expire(tmpSet, 60 * 5)
        self.pipe.execute()
        count = self.redis.scard(tmpSet)
        # print count
        if count == 0:
            return None
        else:
            return tmpSet

    def needTimeFilter(self, conditions):
        return (('starttime' in conditions) or ('endtime' in conditions))

    @dcrator.timeit
    def getTimeFilteredSet(self, conditions):
        '''
        Only the error set in the period.
        Notice:zset has no proper xxxstore method, so the xxxrangexxx method must return the data to the caller.
        TODO: If server load is heavy, the tmp set can be buffered. name the set by time filter,
        such as: tmp_error_1234567890_1234569000
        '''
        try:
            if ('starttime' in conditions) ^ ('endtime' in conditions):
                if 'starttime' in conditions:
                    conditions['endtime'] = '%d' % (time.time())
                else:
                    conditions['starttime'] = (datetime.fromtimestamp(
                        float(conditions['endtime'])) - timedelta(days=90)).strftime('%s')
            start = conditions.pop('starttime')
            end = conditions.pop('endtime')
        except Exception, e:
            print e
            return None

        targetSet = self.redis.zrangebyscore('ss:ids:b', start, end)
        tmpSet = 'tmp_error_%s-%s' % (start, end)

        counter = 0
        for id in targetSet:
            counter += 1
            self.pipe.sadd(tmpSet, id)
            if (counter % 10000 == 0):
                self.pipe.execute()
        self.pipe.expire(tmpSet, 60 * 5)  # expire after 5 mins
        self.pipe.execute()
        count = self.redis.scard(tmpSet)
        # print count
        if count == 0:
            return None
        else:
            return tmpSet

    def export(user, password, product, start_date=None, end_date=None):
        '''
        Data exporting interface for manufacturer.
        Parameters:
        user=username
        password=password
        product=like: BKB
        start_date=like: 20120701
        end_date=like: 20120715(not included)

        Return:
        Headers:
        Content-Type:application/json
        Body:
        {"results":[{},{},...]}
        A json array and every element in the array is a json document.
        array:[{},{}]
        document:{"_id":id,"receive_time":time,"json_str":original}
        '''
        print 'export(),user=%s,product=%s,start=%s,end=%s'%(user, product, start_date, end_date)

        userInfo = {"username": user, "password": password}
        authInfo = proxy.auth(userInfo)
        results = authInfo["results"]
        token = None
        error = None
        if 'token' in results:
            token = results["token"]
        if 'error' in results:
            error = results["error"]

        if (token == None):
            if error != None:
                return error
            else:
                return {"error": "Unknown error"}

        redis = brconfig.getRedis()
        pipe = redis.pipeline(transaction=True)

        ret = []
        sets = []
        # accessibleSet='tmp_%s'%str(uuid.uuid4())
        timeFilteredSet = 'tmp_%s' % str(uuid.uuid4())
        resultIdsSet = 'tmp_%s' % str(uuid.uuid4())

        # Get accessible set
        result = auth.getAccessibleProducts(token)
        if result == None:
            print "No accessible products!"
            return {"error": "No accessible products!"}
        if ('error' in result):
            print "Error in result:%s" % result['error']
            return result
        products = result
        if product not in products:
            return {'error': 'The given product is not in the accessible products list.'}
        sets.append('ids:i:android.os.Build.PRODUCT:%s' % product)

        # Get time filtered set
        starttime = 0
        endtime = 0
        ntf = False
        if start_date != None:
            try:
                starttime = int(
                    datetime.strptime(start_date, "%Y%m%d").strftime('%s'))
                ntf = True
            except ValueError, e:
                print "start_date:%s" % e
                return {'error': 'Invalid format for start_date:%s' % start_date}
        if end_date != None:
            try:
                endtime = int(
                    datetime.strptime(end_date, "%Y%m%d").strftime('%s'))
                ntf = True
            except ValueError, e:
                print "end_date:%s" % e
                return {'error': 'Invalid format for end_date:%s' % end_date}
        if ntf:
            timeFilteredSet = getTimeFilteredSet(
                starttime, endtime, timeFilteredSet)
            if timeFilteredSet == None:
                print "Time Filtered Set is None!"
                return []
            else:
                sets.append(timeFilteredSet)

        pipe.sinter(sets)
        pipe.delete(timeFilteredSet)
        result = pipe.execute()

        retset = list(result[0])
        if len(retset) == 0:
            print 'The result set is empty!'
            return []

        result = proxy.export(retset)
        response.set_header("Content-Type", "application/json")
        return result

    @dcrator.timeit
    def product_summary(self, accessible, platform='4.0.4', callDropMode=False):
        '''
        '''
        MAX_REVISION_COUNT = 10
        accessibleProducts = accessible

        rateLink = "/api/brquery/query/rate?groupby=%s&android.os.Build.VERSION.RELEASE=%s&android.os.Build.PRODUCT=%s&mode=%s"
        if callDropMode:
            mode = "calldrop"
            multiplier = 10
            errorSet = 'ids:b:CALL_DROP'
            baseSet = 'ids:s:com.borqs.bugreporter:CALL_COUNT'
            revisionLink = "/api/brquery/query/error?e_type=CALL_DROP&android.os.Build.VERSION.RELEASE=%s&android.os.Build.PRODUCT=%s&ro.build.revision=%s"
            buildtimeLink = "/api/brquery/query/error?e_type=CALL_DROP&android.os.Build.VERSION.RELEASE=%s&android.os.Build.PRODUCT=%s&android.os.Build.TIME=%s"      
        else:
            mode = "error"
            multiplier = 6
            errorSet = 'ids:e'
            baseSet = 'ids:s:com.borqs.bugreporter:LIVE_TIME'
            revisionLink = "/api/brquery/query/error?android.os.Build.VERSION.RELEASE=%s&android.os.Build.PRODUCT=%s&ro.build.revision=%s"
            buildtimeLink = "/api/brquery/query/error?android.os.Build.VERSION.RELEASE=%s&android.os.Build.PRODUCT=%s&android.os.Build.TIME=%s"

        tmp = 'tmp_%s' % uuid.uuid4()
        productSet = 'ids:%s:%s'

        platProducts = self.redis.smembers('set:%s:product' % platform)
        products = list(set(accessibleProducts) & set(platProducts))
        if len(products) == 0:
            return []
        products.sort()

        total = []
        for product in products:
            errorCount = 0
            baseCount = 0
            productItem = {}
            productItem['product'] = product
            productItem['mode'] = mode
            if self.redis.exists('ss:%s:%s:revision' % (platform, product)):
                verList = self.redis.zrevrangebyscore('ss:%s:%s:revision' % (
                    platform, product), int(time.time() * 1000), 0, 0, MAX_REVISION_COUNT)
                linkTemplate = revisionLink
                verKey = 'revision'
                verSet = 'ids:i:ro.build.revision:%s'
                groupBy = 'ro.build.revision'
            else:
                verList = self.redis.zrevrangebyscore('ss:%s:%s:buildtime' % (
                    platform, product), int(time.time() * 1000), 0, 0, MAX_REVISION_COUNT)
                linkTemplate = buildtimeLink
                verKey = 'buildtime'
                verSet = 'ids:i:android.os.Build.TIME:%s'
                groupBy = 'android.os.Build.TIME'

            sublist = []
            for ver in verList:
                verItem = {}
                errorKeys = [productSet %
                             (platform, product), verSet % ver, errorSet]
                baseKeys = [productSet %
                            (platform, product), verSet % ver, baseSet]
                self.pipe.sinterstore(tmp, errorKeys)
                self.pipe.sinterstore(tmp, baseKeys)
                self.pipe.delete(tmp)
                ret = self.pipe.execute()
                verItem['count'] = ret[0]
                verItem['base'] = ret[1] * multiplier
                errorCount += ret[0]
                baseCount += ret[1]
                if ret[1] == 0:
                    verItem['rate'] = 'N/A'
                else:
                    verItem['rate'] = '%s%%' % (ret[0] * 100 / ret[1])
                verItem[verKey] = ver  # It's better to format it
                verItem['link'] = linkTemplate % (platform, product, ver)
                sublist.append(verItem)
            productItem['sublist'] = sublist
            productItem['count'] = errorCount
            productItem['base'] = baseCount * multiplier
            if baseCount == 0:
                productItem['rate'] = 'N/A'
            else:
                productItem['rate'] = '%s%%' % (
                    errorCount * 100 / productItem['base'])
            productItem['link'] = rateLink % (groupBy, platform, product, mode)
            total.append(productItem)
        self.redis.delete(tmp)
        return total

    @dcrator.timeit
    def rate_summary(self, conditions, group, show_error_type=True):
        print "rate_summary()"

        if 'token' in conditions:
            token = conditions.pop('token')
        else:
            return {"error": {"code": 12, "msg": "Invalid token"}}

        print "rate_summary - conditions:"
        for key in conditions:
            print "%s:%s" % (key, conditions[key])
        print "rate_summary - Group by:%s" % group
        # TODO: Filter result by access right.

        # Get work mode: drop/error
        mode = 'error'
        if 'mode' in conditions:
            mode = conditions.pop('mode')
        if mode != 'calldrop':
            mode = 'error'

        r = self.redis
        pipe = self.pipe

        group_key = group

        pipe.smembers('i:k:%s' % group_key)
        pipe.smembers('b:t')
        group_values, types = pipe.execute()

        print "rate_summary - group values:"
        print group_values

        print "Finish getting the group value and error types."

        if mode == 'calldrop':
            types = ['CALL_DROP']
        else:
            types = list(types)
            types.remove('CALL_DROP')

        # Get time filtered set
        timeFilteredSet = 'tmp_%s' % str(uuid.uuid4())
        starttime = 0
        endtime = 0
        ntf = False
        if 'starttime' in conditions:
            starttime = conditions.pop('starttime')
            ntf = True
        if 'endtime' in conditions:
            endtime = conditions.pop('endtime')
            ntf = True
        if ntf:
            timeFilteredSet = self.getTimeFilteredSet(
                {"starttime": starttime, "endtime": endtime})

        # get all data except uptimes...
        t1 = time.clock()

        new_values = []

        for v in group_values:
            conditions[group_key] = v
            sets = []
            for k, v in conditions.items():
                sets.append('ids:i:%s:%s' % (k, v))
            if ntf:
                sets.append(timeFilteredSet)
            print sets
            pipe.sinter(sets)

        ret = pipe.execute()

        for v in group_values:
            print v
            # print ret[0]
            if len(ret[0]) > 0:
                new_values.append(v)
            ret.pop(0)

        group_values = new_values

        print "New groups:"
        print group_values

        for v in group_values:
            conditions[group_key] = v
            sets = []
            tmpSet = 'tmp_%s' % str(uuid.uuid4())

            for k, v in conditions.items():
                sets.append('ids:i:%s:%s' % (k, v))

            if ntf:
                sets.append(timeFilteredSet)
            pipe.sinterstore(tmpSet, sets)

            if mode == 'error':
                pipe.sinter(tmpSet, 'ids:s:%s:%s' %
                            ('com.borqs.bugreporter', 'LIVE_TIME'))
            else:
                pipe.sinter(tmpSet, 'ids:s:%s:%s' %
                            ('com.borqs.bugreporter', 'CALL_COUNT'))

            if show_error_type:
                for t in types:
                    pipe.sinter(tmpSet, 'ids:b:%s' % t)
            else:
                pipe.sinter(tmpSet, 'ids:e')

            pipe.delete(tmpSet)

        if ntf:
            pipe.delete(timeFilteredSet)

        ret = pipe.execute()

        print "Finish getting all the data..."

        t2 = time.clock()

        # go through all results and get uptime data
        cur_ret = ret
        for v in group_values:
            time_ids = cur_ret[1]
            if len(time_ids) > 0:
                pipe.hmget('s:values', time_ids)
                print "---- s:values: v: %s" % v
                print time_ids
            cur_ret = show_error_type and cur_ret[
                3 + len(types):] or cur_ret[4:]
        times = pipe.execute()  # to get all uptimes in one execute.

        print "Finish getting all the uptime."
        t3 = time.clock()

        # go through all results and get the data
        results = []
        for v in group_values:
            inter_num = ret[0]
            time_ids = ret[1]
            if inter_num > 0:  # not empty
                uptime = 0
                if len(time_ids) > 0:
                    cur_times = times[0]
                    if mode == "error":
                        uptime = sum(long(t) for t in cur_times) / 3600.
                    else:
                        uptime = sum(int(t) for t in cur_times)

                if show_error_type:
                    cur_bugs = ret[2:2 + len(types)]
                    l = map(
                        lambda t, s: {'g_value': v, 'livetime': uptime, 'e_type': t, 'e_count': len(s)}, types, cur_bugs)
                else:
                    l = [
                        {'g_value': v, 'livetime': uptime, 'e_count': len(ret[2])}]
                errors = filter(lambda o: o['e_count'] != 0, l)
                if uptime > 0 and len(errors) == 0: # we should return the non-zero uptime in case of errors is empty 
                    if show_error_type:
                        errors.append(
                            {'g_value': v, 'livetime': uptime, 'e_count': 0, 'e_type': ''})
                    else:
                        errors.append(
                            {'g_value': v, 'livetime': uptime, 'e_count': 0})

                results += errors
            ret = show_error_type and ret[3 + len(types):] or ret[4:]
            times = times[len(time_ids) and 1 or 0:]

        print "Finish analyzing the data."

        t4 = time.clock()
        return results

    # return a float value, sum for phone uptime filtered by param conditions
    def live_time(conditions):
        r = brconfig.getRedis()
        sets = ['ids:i:%s:%s' % (k, v) for k, v in conditions.items()]
        sets.append('ids:s:%s:%s' % ('com.borqs.bugreporter', 'LIVE_TIME'))
        time_ids = r.sinter(sets)
        if len(time_ids) > 0:
            uptimes = r.hmget('s:values', time_ids)
            return sum(long(t) for t in uptimes) / 3600.
        else:
            return 0

    #[{'e_type':'...', 'e_count':.}, {}, ...]
    def error_count(conditions, show_error_type=True):
        r = brconfig.getRedis()
        sets = ['ids:i:%s:%s' % (k, v) for k, v in conditions.items()]
        if show_error_type:
            types = r.smembers('b:t')
            pipe = r.pipeline(transaction=True)
            for t in types:
                pipe.sinter(s for s in sets + ['ids:b:%s' % t])
            errors = pipe.execute()
            l = map(
                lambda t, e: {'e_type': t, 'e_count': len(e)}, types, errors)
        else:
            l = [{'e_count': len(r.sinter(s for s in sets + ['ids:b']))}]
        return filter(lambda o: o['e_count'] != 0, l)

    #[{'e_type':'...', 'uptime':., 'e_count':.}, {}, ...]
    def error_rate(conditions, show_error_type=True):
        errors = error_count(conditions, show_error_type)
        lt = live_time(conditions)
        for e in errors:
            e['uptime'] = lt
        if lt > 0 and len(errors) == 0:
            errors.append({'uptime': lt})
        return errors

    # generate excel for error list
    def error_list_excel(self, data):
        # datas=data['results']
        w = Workbook()
        ws = w.add_sheet('error_list')
        # set content font
        font = Font()
        font.name = "Arial"

        # set borders
        borders = Borders()
        borders.left = 1
        borders.right = 1
        borders.top = 1
        borders.bottom = 1

        al = Alignment()
        al.horz = Alignment.HORZ_CENTER
        al.vert = Alignment.VERT_CENTER
        style = XFStyle()
        style.font = font
        style.alignment = al
        style.borders = borders

        # set header font
        font1 = Font()
        font1.name = "Arial"
        font1.bold = True

        style1 = XFStyle()
        style1.font = font1
        style1.alignment = al
        style1.borders = borders

        ws.write(0, 0, 'ID', style1)
        ws.write(0, 1, 'Receive_Time', style1)
        ws.write(0, 2, 'Error_Type', style1)
        ws.write(0, 3, 'Name', style1)
        ws.write(0, 4, 'Description', style1)
        ws.write(0, 5, 'PhoneNumber', style1)
        ws.write(0, 6, 'Revision', style1)

        j = 1
        for record in data:
            ws.write(j, 0, record['_id'], style)
            ws.write(j, 1, record['receive_time'], style)
            ws.write(j, 2, record['type'], style)
            ws.write(j, 3, record['name'], style)
            ws.write(j, 4, record['info'], style)
            ws.write(j, 5, record['sys_info']['phoneNumber'], style)
            ws.write(j, 6, record['sys_info']['ro.build.revision'], style)
            j = j + 1

        # response.set_header('Content-Type','application/vnd.ms-excel')
        # response.set_header("Content-Disposition",
        # "attachment;filename=errorlist.xls");
        return w.get_biff_data()

    def get_accessible_ids(token, ids=None):
        tmpSetName = 'tmp_%s' % str(uuid.uuid4())
        tmpSetName = getAccessibleSet(token, tmpSetName, ids=ids)
        if tmpSetName == None:
            return None
        else:
            redis = brconfig.getRedis()
            ret_ids = redis.smembers(tmpSetName)
            redis.delete(tmpSetName)
            return ret_ids

    def summary(self, conditions):
        '''
        '''
        data = {}
        if "year" in conditions:
            return self.getYearData(conditions["year"])
        elif "month" in conditions:
            return self.getMonthData(conditions["month"])
        elif "phonenumber" in conditions:
            return self.getUserData(phonenumber=conditions["phonenumber"])
        elif "imsi" in conditions:
            return self.getUserData(imsi=conditions["imsi"])
        return data

    def getDataInPeriod(self, period):
        '''
        ZCOUNT key min max
        ss:ids:e
        ss:ids:LIVE_TIME
        '''
        if len(period) == 4:
            isYear = True
            formatStr = '%Y'
            timeStep = 0  # Not fixed
        elif len(period) == 6:
            isYear = False
            formatStr = '%Y%m'
            timeStep = 3600 * 24
        else:
            return {"error": "Invalid parameter:%s" % period}

        try:
            startDay = datetime.strptime(period, formatStr)
        except ValueError, ve:
            return {"error": "Invalid parameter:%s" % period}

        if isYear or startDay.month == 12:
            endDay = datetime(startDay.year + 1, 1, 1)
        else:
            endDay = datetime(startDay.year, startDay.month + 1, 1)

        starttime = int(startDay.strftime('%s'))
        endtime = int(endDay.strftime('%s'))

        timeList = []
        day = starttime
        if isYear:
            for i in range(12):
                start = int(
                    datetime(startDay.year, startDay.month + i, 1).strftime('%s'))
                if i == 11:
                    end = endtime
                else:
                    end = int(
                        datetime(startDay.year, startDay.month + (i + 1), 1).strftime('%s'))
                timeList.append((start, end))
        else:
            while (day < endtime):
                timeList.append((day, day + timeStep))
                day += timeStep

        for (start, end) in timeList:
            self.pipe.zcount('ss:ids:e', start, end)
            self.pipe.zcount('ss:ids:s:LIVE_TIME', start, end)
        ret = self.pipe.execute()

        data = {}
        for i in range(len(timeList)):
            if i < 9:
                dateStr = '%s0%s' % (period, i + 1)
            else:
                dateStr = '%s%s' % (period, i + 1)
            data['%s' % (i + 1)] = {"error": int(ret[i * 2]), "live": int(
                ret[i * 2 + 1]), "link": "errors?date=%s" % dateStr}
        return data

    @dcrator.timeit
    def getMonthData(self, month):
        return self.getDataInPeriod(month)

    @dcrator.timeit
    def getYearData(self, year):
        return self.getDataInPeriod(year)

    @dcrator.timeit
    def getUserData(self, phonenumber=None, imsi=None):
        if phonenumber is None and imsi is None:
            return {"error": "Invalid parameter."}

        keyName = None
        backupKeyName = None

        if phonenumber is not None:
            user = phonenumber
            queryUrl = "errors?phoneNumber=%s&date=" % user
            keyName = "ids:i:phoneNumber:%s" % phonenumber
            backupKeyName = "ids:i:phoneNumber:+86%s" % phonenumber
        else:
            user = imsi
            queryUrl = "errors?imsi=%s&date=" % user
            keyName = "ids:i:phoneNumber:IMSI:%s" % imsi

        ret = self.redis.exists(keyName)
        if not ret:
            keyName = backupKeyName
            ret = self.redis.exists(keyName)
            if not ret:
                return {"error": {'code': 0, 'msg': "No data for the given number."}}

        end = int(date.today().strftime('%s')) + 3600 * 24
        start = end - 3600 * 24 * 30
        eRet = self.redis.zrangebyscore('ss:ids:e', start, end, start=0, num=1)
        lRet = self.redis.zrangebyscore(
            'ss:ids:s:LIVE_TIME', start, end, start=0, num=1)

        el = list(eRet)
        ll = list(lRet)
        eMin = -1
        lMin = -1
        if len(el) != 0:
            eMin = el[0]
        if len(ll) != 0:
            lMin = ll[0]
        if eMin == -1 and lMin == -1:
            return {"error": {'code': 0, 'msg': "No data for recent 30 days."}}

        minId = min(int(eMin), int(lMin))

        ids = self.redis.sort(keyName)
        if len(ids) == 0:
                return {"error": {'code': 0, 'msg': "No data for the given number."}}
        try:
            while(int(ids[0]) < minId):
                ids.pop(0)
        except:
            return {"error": {'code': 0, 'msg': "No data for the given number in recent 30 days."}}
        return ids

    '''
    ********************************************************************************************************************************
    '''

    '''
    ********************************************************************************************************************************
    '''

if (__name__ == '__main__'):
    viewer = Viewer()
    # ret=viewer.getMonthData('201302')
    # ret=viewer.getYearData('2013')
    # ret=viewer.getUserData(phonenumber='18612345678')
    accessible = ['BP710A', 'yukkabeach', 'BKB', 'AZ210A', "RHB", "THTEST"]
    platform = '4.1.2'
    callDropMode = False
    # ret=viewer.product_summary(accessible,platform)
    # print len(ret)
    # conditions={'endtime':'1356969600'}#,'endtime':'1362844800'}
    # ret=viewer.getTimeFilteredSet(conditions)
    ret = viewer.getAccessibleSet(accessible)
    print ret
