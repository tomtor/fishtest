#!/usr/bin/python
import os
import sys
import fcntl

from datetime import datetime, timedelta

# For tasks
sys.path.append(os.path.expanduser('~/fishtest/fishtest'))
from fishtest.rundb import RunDb
from fishtest.views import parse_tc, delta_date

def process_run(run, info, last_process_date=None):
  if 'deleted' in run:
    return
  if last_process_date and run['last_updated'] < last_process_date:
    return
  if 'username' in run['args']:
    username = run['args']['username']
    info[username]['tests'] += 1

  tc = parse_tc(run['args']['tc'])
  for task in run['tasks']:
    if 'worker_info' not in task:
      continue
    username = task['worker_info'].get('username', None)
    if username == None:
      continue

    if 'stats' in task:
      stats = task['stats']
      num_games = stats['wins'] + stats['losses'] + stats['draws']
    else:
      num_games = task['num_games']

    try:
      info[username]['last_updated'] = max(task['last_updated'], info[username]['last_updated'])
    except:
      info[username]['last_updated'] = task['last_updated']

    info[username]['cpu_hours'] += float(num_games * int(run['args'].get('threads', 1)) * tc / (60 * 60))
    info[username]['games'] += num_games

def build_users(machines, info):
  for machine in machines:
    games_per_hour = (machine['nps'] / 1200000.0) * (3600.0 / parse_tc(machine['run']['args']['tc'])) * int(machine['concurrency'])
    info[machine['username']]['games_per_hour'] += games_per_hour

  users = []
  for u in info.keys():
    user = info[u]
    try:
      user['last_updated'] = delta_date(user['last_updated'])
    except:
      pass
    users.append(user)

  users = [u for u in users if u['games'] > 0 or u['tests'] > 0]
  return users

def update_users():
  rundb = RunDb()

  info = {}
  top_month = {}

  last_stats = datetime.min
  clear_stats = True
  if len(sys.argv) > 1:
    print('scan all')
  else:
    for stat in rundb.actiondb.get_actions(1, 'update_stats'):
      last_stats = stat['time']
      clear_stats = False
  print('last: ' + str(last_stats))

  for u in rundb.userdb.get_users():
    username = u['username']
    top_month[username] = {'username': username,
                      'cpu_hours': 0,
                      'games': 0,
                      'tests': 0,
                      'tests_repo': u.get('tests_repo', ''),
                      'last_updated': datetime.min,
                      'games_per_hour': 0.0,}
    if clear_stats:
      info[username] = top_month[username].copy()
    else:
      info[username] = rundb.userdb.user_cache.find_one({'username': username})

  for run in rundb.get_unfinished_runs():
    process_run(run, top_month)

  # Step through these 100 at a time to avoid using too much RAM
  current = 0
  step_size = 100
  now = datetime.utcnow()

  # prevent race condition with 'stop_run' in server
  fcntl.flock(RunDb.lock_file, fcntl.LOCK_EX)
  # record this update run
  rundb.actiondb.update_stats()

  more_days = True
  first = True
  while more_days:
    runs = rundb.get_finished_runs(skip=current, limit=step_size)[0]
    if first:
      fcntl.flock(RunDb.lock_file, fcntl.LOCK_UN)
      first = False
      print('race window: ' + str(datetime.utcnow() - now))
    if len(runs) == 0:
      break
    for run in runs:
      process_run(run, info, last_stats)
      if (now - run['start_time']).days < 31:
        process_run(run, top_month)
      elif not clear_stats:
        more_days = False
    current += step_size

  machines = rundb.get_machines()

  users = build_users(machines, info)
  rundb.userdb.user_cache.remove()
  rundb.userdb.user_cache.insert(users)

  rundb.userdb.top_month.remove()
  rundb.userdb.top_month.insert(build_users(machines, top_month))

  # Delete users that have never been active and old admins group
  idle = {}
  for u in rundb.userdb.get_users():
      update = False
      while 'group:admins' in u['groups']:
          u['groups'].remove('group:admins')
          update = True
      if update:
        rundb.userdb.users.save(u)
      if not 'registration_time' in u \
         or u['registration_time'] < datetime.utcnow() - timedelta(days=28):
        idle[u['username']] = u
  for u in rundb.userdb.user_cache.find():
    if u['username'] in idle:
      del idle[u['username']]
  for u in idle.values():
    # A safe guard against deleting long time users
    if not 'registration_time' in u \
      or u['registration_time'] < datetime.utcnow() - timedelta(days=38):
        print('Warning: Found old user to delete: ' + u['_id'])
    else:
      print('Delete: ' + u['_id'])
      rundb.userdb.users.remove({'_id': u['_id']})

  print('Successfully updated %d users' % (len(users)))

def main():
  update_users()

if __name__ == '__main__':
  main()
