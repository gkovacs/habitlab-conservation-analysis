#!/usr/bin/env python
# md5: 4c549147818d32063921e34b901c140a
#!/usr/bin/env python
# coding: utf-8



import json
import urllib.request as req
from memoize import memoize # pip install memoize2
from pymongo import MongoClient
from getsecret import getsecret
import urllib.parse
import moment
import datetime



#def get_user_to_all_install_ids():
#  user_to_install = json.loads(req.urlopen("http://localhost:5001/get_user_to_all_install_ids").read().decode("utf-8"))
#  return user_to_install

#def get_collection_names():
#  collection_names = json.loads(req.urlopen("http://localhost:5001/listcollections").read().decode("utf-8"))
#  return collection_names

def get_session_info_list_for_user(userid):
  output = json.loads(req.urlopen("http://localhost:5001/get_session_info_list_for_user?userid=" + userid).read().decode("utf-8"))
  return output



#collection_names = get_collection_items('collections')
#print(len(collection_names))
#print(get_collection_for_user('e0ea34c81d4b50cddc7bd752', 'synced:seconds_on_domain_per_session')[0])



@memoize
def download_url(url):
  return req.urlopen(url).read().decode("utf-8")

def getjson(path, params={}):
  querystring = urllib.parse.urlencode(params)
  url = 'http://localhost:5001/' + path + '?' + querystring
  return json.loads(download_url(url))

def make_getjson_func(path, *param_list):
  def f(*arg_list):
    if len(param_list) != len(arg_list):
      print('missing some number of arguments. expected parameters: ' + str(param_list))
    param_dict = {}
    for param,arg in zip(param_list, arg_list):
      param_dict[param] = arg
    return getjson(path, param_dict)
  return f

def expose_getjson(func_name, *args):
  f = make_getjson_func(func_name, *args)
  globals()[func_name] = f
  return f  



expose_getjson('get_session_info_list_for_user', 'userid')
#expose_getjson('get_user_to_all_install_ids')

#print(get_user_to_all_install_ids()['e0ea34c81d4b50cddc7bd752'])
#get_session_info_list = make_getjson_func('get_session_info_list_for_user', 'userid')
#print(get_session_info_list_for_user('e0ea34c81d4b50cddc7bd752')[0])
#def get_user_to_all_install_ids(user):
#  return getjson



@memoize
def get_db(): # this is for the browser
  client = MongoClient(getsecret("EXT_URI"))
  db = client[getsecret("DB_NAME")]
  return db

@memoize
def get_collection_items(collection_name):
  db = get_db()
  return [x for x in db[collection_name].find({})]

def get_collection_for_user(user, collection_name):
  return get_collection_items(user + '_' + collection_name)



def get_collection_names():
  collection_names = get_collection_items('collections')
  return [x['_id'] for x in collection_names]

def get_users_with_goal_frequency_set():
  output = []
  collection_names = get_collection_names()
  for collection_name in collection_names:
    if not collection_name.endswith('_synced:goal_frequencies'):
      continue
    username = collection_name.replace('_synced:goal_frequencies', '')
    output.append(username)
  return output



@memoize
def get_user_to_all_install_ids():
  install_info_list = get_collection_items('installs')
  output = {}
  for install_info in install_info_list:
    if 'user_id' not in install_info:
      continue
    user_id = install_info['user_id']
    install_id = install_info.get('install_id', None)
    if user_id not in output:
      output[user_id] = []
    if install_id not in output[user_id]:
      output[user_id].append(install_id)
  return output

#print(get_user_to_all_install_ids()['e0ea34c81d4b50cddc7bd752'])



@memoize
def get_all_install_ids_for_user(user):
  seconds_on_domain_per_session = get_collection_for_user(user, 'synced:seconds_on_domain_per_session')
  interventions_active_for_domain_and_session = get_collection_for_user(user, 'synced:interventions_active_for_domain_and_session')
  user_to_all_install_ids = get_user_to_all_install_ids()
  output = []
  output_set = set()
  if user in user_to_all_install_ids:
    for install_id in user_to_all_install_ids[user]:
      if install_id not in output_set:
        output_set.add(install_id)
        output.append(install_id)
  for item in seconds_on_domain_per_session:
    if 'install_id' not in item:
      continue
    install_id = item['install_id']
    if install_id not in output_set:
      output_set.add(install_id)
      output.append(install_id)
  for item in interventions_active_for_domain_and_session:
    if 'install_id' not in item:
      continue
    install_id = item['install_id']
    if install_id not in output_set:
      output_set.add(install_id)
      output.append(install_id)
  return output

@memoize
def get_is_valid_user(user):
  install_ids = get_all_install_ids_for_user(user)
  if len(install_ids) != 1:
    return False
  return True

@memoize
def get_valid_user_list():
  user_list = get_users_with_goal_frequency_set()
  output = []
  for user in user_list:
    if not get_is_valid_user(user):
      continue
    output.append(user)
  return output

#get_sessions_for_user('e0ea34c81d4b50cddc7bd752')
#valid_user_list = get_valid_user_list()
#print(len(valid_user_list))



'''
function convert_date_to_epoch(date) {
  let start_of_epoch = moment().year(2016).month(0).date(1).hours(0).minutes(0).seconds(0).milliseconds(0)
  let year = parseInt(date.substr(0, 4))
  let month = parseInt(date.substr(4, 2)) - 1
  let day = parseInt(date.substr(6, 2))
  let date_moment = moment().year(year).month(month).date(day).hours(0).minutes(0).seconds(0).milliseconds(0)
  return date_moment.diff(start_of_epoch, 'days')
}

function convert_epoch_to_date(epoch) {
  let start_of_epoch = moment().year(2016).month(0).date(1).hours(0).minutes(0).seconds(0).milliseconds(0)
  start_of_epoch.add(epoch, 'days')
  return start_of_epoch.format('YYYYMMDD')
}

function timestamp_to_epoch(timestamp) {
  let start_of_epoch = moment().year(2016).month(0).date(1).hours(0).minutes(0).seconds(0).milliseconds(0)
  return moment(timestamp).diff(start_of_epoch, 'days')
}
'''

def convert_date_to_epoch(date):
  start_of_epoch = moment.now().timezone("US/Pacific").replace(years=2016, months=1, days=1, hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0)
  year = int(date[0:4])
  month = int(date[4:6])
  day = int(date[6:8])
  date_moment = moment.now().timezone("US/Pacific").replace(years=year, months=month, days=day, hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0)
  return date_moment.diff(start_of_epoch).days

def convert_epoch_to_date(epoch):
  start_of_epoch = moment.now().timezone("US/Pacific").replace(years=2016, months=1, days=1, hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0)
  start_of_epoch.add(days=epoch)
  return start_of_epoch.format('YYYYMMDD')

def timestamp_to_epoch(timestamp):
  start_of_epoch = moment.now().timezone("US/Pacific").replace(years=2016, months=1, days=1, hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0)
  return moment.unix(timestamp).timezone("US/Pacific").diff(start_of_epoch).days

def timestamp_to_isoweek(timestamp):
  isoWeek = int(datetime.datetime.fromtimestamp(timestamp/1000).isocalendar()[1]) 
  return isoWeek

def epoch_to_isoweek(epoch):
  start_of_epoch = moment.now().timezone("US/Pacific").replace(years=2016, months=1, days=1, hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0)
  start_of_epoch.add(days=epoch)
  timestamp_seconds = start_of_epoch.epoch()
  isoWeek = int(datetime.datetime.fromtimestamp(timestamp_seconds).isocalendar()[1])
  return isoWeek

#print(timestamp_to_epoch(1537059309631))
#print(convert_epoch_to_date(988))
#print(convert_date_to_epoch('20180915'))
#print(convert_date_to_epoch('20180917'))
#print(epoch_to_isoweek(990))



#a=moment.unix(1537221946630)
#dir(a)
#print(timestamp_to_isoweek(1537221946630))



@memoize
def get_frequency_info_for_user_epoch(user, epochnum):
  # returns a dictionary mapping goal name -> 1 if frequent, 0 if infrequent
  isoweek_input = epoch_to_isoweek(epochnum)
  goal_frequencies = get_collection_for_user(user, 'synced:goal_frequencies')
  output = {}
  conflict_info_list = []
  for item in goal_frequencies:
    timestamp_local = item['timestamp_local']
    isoweek_local = timestamp_to_isoweek(timestamp_local)
    algorithm_info = json.loads(item['val'])
    algorithm_name = algorithm_info['algorithm']
    onweeks = algorithm_info['onweeks']
    timestamp = algorithm_info['timestamp']
    if algorithm_name == 'isoweek_random':
      is_frequent = onweeks[isoweek_input] == 1
    elif algorithm_name == 'isoweek_alternating':
      is_frequent = isoweek_input % 2 == onweeks
    else:
      raise Exception('unknown frequency selection algorithm ' + algorithm)
    goal = item['key']
    if goal in output:
      conflict_info = {'item': item, 'existing_is_frequent': output[goal], 'is_frequent': is_frequent}
      conflict_info_list.append(conflict_info)
      continue
    output[goal] = is_frequent
    #print(goal)
    #print(is_frequent)
    #print(algorithm_info)
    #print(item)
  return output

def get_is_goal_frequent_for_user_on_domain_at_epoch(user, target_domain, epochnum):
  goal_to_frequency_info = get_frequency_info_for_user_epoch(user, epochnum)
  for goal_name,is_frequent in goal_to_frequency_info.items():
    domain = get_domain_for_goal(goal_name)
    if domain == target_domain:
      return is_frequent
  # we probably shouldn't have gotten here
  return False
  

#def get_frequency_info_for_goal_on_timestamp(user, goal, )

#print(get_frequency_info_for_user_epoch('c11e5f2d93f249b5083989b2', 990))
#print(get_is_goal_frequent_for_user_on_domain_at_epoch('c11e5f2d93f249b5083989b2', 'www.youtube.com', 990))



@memoize
def get_goals_enabled_for_user_sorted_by_timestamp(user):
  goal_info_list = get_collection_for_user(user, 'logs:goals')
  goal_info_list_sorted = []
  for goal_info in goal_info_list:
    if 'timestamp_local' not in goal_info:
      continue
    goal_info_list_sorted.append(goal_info)
  goal_info_list_sorted.sort(key=lambda k: k['timestamp_local'])
  return goal_info_list_sorted

def get_goals_enabled_for_user_at_timestamp(user, target_timestamp_local):
  goal_info_list_sorted = get_goals_enabled_for_user_sorted_by_timestamp(user)
  enabled_goals = {}
  for goal_info in goal_info_list_sorted:
    # note this can be replaced with binary search if it is slow
    timestamp_local = goal_info['timestamp_local']
    if timestamp_local > target_timestamp_local:
      return enabled_goals
    enabled_goals = goal_info['enabled_goals']
  return enabled_goals

def get_is_goal_enabled_for_user_at_timestamp(user, target_goal_name, target_timestamp_local):
  goals_enabled_dictionary = get_goals_enabled_for_user_at_timestamp(user, target_timestamp_local)
  for goal_name,is_enabled in goals_enabled_dictionary.items():
    if goal_name == target_goal_name:
      return is_enabled
  return False

def get_is_goal_enabled_for_user_on_domain_at_timestamp(user, target_domain, target_timestamp_local):
  goals_enabled_dictionary = get_goals_enabled_for_user_at_timestamp(user, target_timestamp_local)
  for goal_name,is_enabled in goals_enabled_dictionary.items():
    domain = get_domain_for_goal(goal_name)
    if domain == target_domain:
      return is_enabled
  return False
    
#print(get_goals_enabled_for_user_sorted_by_timestamp('c11e5f2d93f249b5083989b2')[0])
#print(get_goals_active_for_user_at_timestep('c11e5f2d93f249b5083989b2', 1533450980492.0))



@memoize
def get_goal_intervention_info():
  return json.load(open('goal_intervention_info.json'))

@memoize
def get_goal_info_list():
  goal_intervention_info = get_goal_intervention_info()
  return goal_intervention_info['goals']

@memoize
def get_goal_info_dict():
  goal_info_list = get_goal_info_list()
  output = {}
  for goal_info in goal_info_list:
    goal_name = goal_info['name']
    output[goal_name] = goal_info
  return output

@memoize
def get_domain_for_goal(goal_name):
  goal_info_dict = get_goal_info_dict()
  if goal_name in goal_info_dict:
    return goal_info_dict[goal_name]['domain']
  if goal_name.startswith('custom/spend_less_time_'): # custom/spend_less_time_www.tumblr.com
    return goal_name[23:] # 23 == len('custom/spend_less_time_www.tumblr.com')
  raise Exception('could not find domain for goal ' + goal_name)

#get_goal_info_dict()
#print(get_domain_for_goal('youtube/spend_less_time'))
#print(get_domain_for_goal('custom/spend_less_time_www.tumblr.com'))



def get_sessions_for_user(user):
  seconds_on_domain_per_session = get_collection_for_user(user, 'synced:seconds_on_domain_per_session')
  interventions_active_for_domain_and_session = get_collection_for_user(user, 'synced:interventions_active_for_domain_and_session')
  #print(seconds_on_domain_per_session[0])
  #print(interventions_active_for_domain_and_session[0])
  output = []
  domain_to_session_id_to_duration_info = {}
  domain_to_session_id_to_intervention_info = {}
  interventions_deployed_with_no_duration_info = []
  seconds_on_domain_per_session.sort(key=lambda k: k['timestamp_local'])
  for item in seconds_on_domain_per_session:
    domain = item['key']
    session_id = item['key2']
    if domain not in domain_to_session_id_to_duration_info:
      domain_to_session_id_to_duration_info[domain] = {}
    domain_to_session_id_to_duration_info[domain][session_id] = item
  for item in interventions_active_for_domain_and_session:
    domain = item['key']
    session_id = item['key2']
    if domain not in domain_to_session_id_to_intervention_info:
      domain_to_session_id_to_intervention_info[domain] = {}
    domain_to_session_id_to_intervention_info[domain][session_id] = item
  for item in seconds_on_domain_per_session:
    #print(item)
    domain = item['key']
    duration = item['val']
    is_goal = False
    local_timestamp = item['timestamp_local']
    local_epoch = timestamp_to_epoch(local_timestamp)
    interventions_active_info = None
    interventions_active_list = None
    intervention_active = None
    if (domain in domain_to_session_id_to_intervention_info) and (session_id in domain_to_session_id_to_intervention_info[domain]):
      interventions_active_info = domain_to_session_id_to_intervention_info[domain][session_id]
      interventions_active_list = json.loads(interventions_active_info['val'])
      if len(interventions_active_list) > 0:
        intervention_active = interventions_active_list[0]
    goals_enabled = get_goals_enabled_for_user_at_timestamp(user, local_timestamp)
    is_goal_enabled = get_is_goal_enabled_for_user_on_domain_at_timestamp(user, domain, local_timestamp)
    is_goal_frequent = get_is_goal_frequent_for_user_on_domain_at_epoch(user, domain, local_epoch)
    goal_to_frequency_info = get_frequency_info_for_user_epoch(user, local_epoch)
    output.append({
      'domain': domain,
      'is_goal_enabled': is_goal_enabled,
      'is_goal_frequent': is_goal_frequent,
      'intervention_active': intervention_active,
      'duration': duration,
      'local_timestamp': local_timestamp,
      'local_epoch': local_epoch,
    })
    #if interventions_active_info != None and interventions_active_list != None and len(interventions_active_list) > 0:
    #  print(domain)
    #  print(is_goal_enabled)
    #  print(intervention_active)
    #  print(duration)
    #  print(is_goal_frequent)
    #  print(goals_enabled)
    #  print(goal_to_frequency_info)
    #  return
  #  duration = item['val']
  #  print(duration)
  return output

#print(get_sessions_for_user('c11e5f2d93f249b5083989b2'))



#all_sessions_info_list = []
#for user in get_valid_user_list():
#  print(user)
#  for info in get_sessions_for_user(user):
#    info['user'] = user
#    all_sessions_info_list.append(info)
    



def group_sessions_by_domain(session_info_list):
  output = {}
  for item in session_info_list:
    domain = item['domain']
    if domain not in output:
      output[domain] = []
    output[domain].append(item)
  return output

def group_sessions_by_epoch(session_info_list):
  output = {}
  for item in session_info_list:
    epoch = item['local_epoch']
    if epoch not in output:
      output[epoch] = []
    output[epoch].append(item)
  return output

def get_sessions_for_user_by_day_and_goal(user):
  session_info_list = get_sessions_for_user(user)
  for epoch,session_info_list_for_day in group_sessions_by_epoch(session_info_list).items():
    for domain,session_info_list_for_domain in group_sessions_by_domain(session_info_list_for_day).items():
      other_goal_domain_total_time = 0
      
      print(epoch)
      print(domain)
      print(session_info_list)
      return
  return

get_sessions_for_user_by_day_and_goal('c11e5f2d93f249b5083989b2')



# def get_days_and_sessions_for_user(user):
#   session_info_list = get_sessions_for_user(user)
#   min_epoch = min([x['local_epoch'] for x in session_info_list])
#   max_epoch = max([x['local'] for x in session_info_list])
#   for epoch in range(min_epoch, max_epoch + 1):
    

# print(get_days_and_sessions_for_user('c11e5f2d93f249b5083989b2'))



#print(len(get_users_with_goal_frequency_set()))
#print(valid_user_list[0])



def print_stats_on_install_records():
  user_to_all_install_ids = get_user_to_all_install_ids()
  users_with_goal_frequency_set = get_users_with_goal_frequency_set()
  users_with_missing_install_record = []
  users_with_zero_installs = []
  users_with_multiple_installs = []
  users_with_single_install = []

  for username in users_with_goal_frequency_set:
    if username not in user_to_all_install_ids:
      users_with_missing_install_record.append(username)
      continue
    install_ids = user_to_all_install_ids[username]
    if len(install_ids) == 0:
      users_with_zero_installs.append(username)
      continue
    if len(install_ids) > 1:
      users_with_multiple_installs.append(username)
      continue
    users_with_single_install.append(username)

  print('users with missing install record', len(users_with_missing_install_record))
  print('users with zero installs', len(users_with_zero_installs))
  print('users with multiple installs', len(users_with_multiple_installs))
  print('users with single install', len(users_with_single_install))


#print_stats_on_install_records()





