#!/usr/bin/env python
# md5: 23d41e9af09a4970425546e78b65a22a
#!/usr/bin/env python
# coding: utf-8



import json
import urllib.request as req



def get_user_to_all_install_ids():
  user_to_install = json.loads(req.urlopen("http://localhost:5001/get_user_to_all_install_ids").read().decode("utf-8"))
  return user_to_install

def get_collection_names():
  collection_names = json.loads(req.urlopen("http://localhost:5001/listcollections").read().decode("utf-8"))
  return collection_names

def get_users_with_goal_frequency_set():
  output = []
  collection_names = get_collection_names()
  for collection_name in collection_names:
    if not collection_name.endswith('_synced:goal_frequencies'):
      continue
    username = collection_name.replace('_synced:goal_frequencies', '')
    output.append(username)
  return output

def get_session_info_list_for_user(userid):
  output = json.loads(req.urlopen("http://localhost:5001/get_session_info_list_for_user?userid=" + userid).read().decode("utf-8"))
  return output



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





