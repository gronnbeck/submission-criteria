# -*- coding: utf-8 -*-
"""Numerai API Testing."""

# System
import zipfile
from datetime import datetime, timedelta

# Third Party
import requests
import numpy as np


class NumerAPI(object):
    def __init__(self):
        api_url = "https://stage-api-numer-ai.herokuapp.com"
        new_api_url = "https://stage-api-hs-numerai.herokuapp.com"
        self._login_url = api_url + '/sessions'
        self._auth_url = api_url + '/upload/auth'
        self._dataset_url = api_url + '/competitions/current/dataset'
        self._submissions_url = api_url + '/submissions'
        self._users_url = api_url + '/users'
        self.leaderboard_url = api_url + '/competitions'
        self.new_leaderboard_url = new_api_url + '/leaderboard'
        self.new_current_leaderboard_url = new_api_url + '/currentLeaderboard'
        self._credentials = None

    @property
    def credentials(self):
        if not hasattr(self, "_credentials"):
            raise ValueError("You haven't yet set your email and password credentials.  Set it first with NumeraAPI().credentials = ('YOUR_EMAIL', 'YOUR_PASSWORD')")
        return self._credentials

    @credentials.setter
    def credentials(self, value):
        self._credentials = {"email": value[0], "password": value[1]}

    def download_current_dataset(self, dest_path='.', unzip=True):
        file_name = 'numerai_dataset.zip'
        dest_file_path = '{0}/{1}'.format(dest_path, file_name)

        r = requests.get(self._dataset_url, stream=True)
        if r.status_code != 200:
            return r.status_code

        with open(dest_file_path, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        if unzip:
            with zipfile.ZipFile(dest_file_path, "r") as z:
                z.extractall(dest_path)
        return r.status_code

    def get_new_leaderboard(self, n=None):
        if n is None:
            url = self.new_current_leaderboard_url
        else:
            url = self.new_leaderboard_url + "?round={}".format(n)
        r = requests.get(url)
        return (r.json(), r.status_code)

    def get_leaderboard(self):
        now = datetime.now()
        tdelta = timedelta(microseconds=55296e5)
        dt = now - tdelta
        dt_str = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        url = self.leaderboard_url + '?{ leaderboard :'
        url += ' current , end_date :{ $gt : %s }}'
        r = requests.get((url % (dt_str)).replace(' ', '%22'))
        if r.status_code != 200:
            return (None, r.status_code)
        return (r.json(), r.status_code)

    def get_earnings_per_round(self, username):
        r = requests.get('{0}/{1}'.format(self._users_url, username))
        if r.status_code != 200:
            return (None, r.status_code)

        rj = r.json()
        rewards = rj['rewards']
        earnings = np.zeros(len(rewards))
        for i, _ in enumerate(rewards):
            earnings[i] = rewards[i]['amount']
        return (earnings, r.status_code)

    def get_scores(self, username):
        r = requests.get('{0}/{1}'.format(self._users_url, username))
        if r.status_code != 200:
            return (None, r.status_code)

        rj = r.json()
        results = rj['submissions']['results']
        scores = np.zeros(len(results))
        for i, _ in enumerate(results):
            scores[i] = results[i]['accuracy_score']
        return (scores, r.status_code)

    def get_user(self, username):
        leaderboard, status_code = self.get_leaderboard()
        if status_code != 200:
            return (None, None, None, None, status_code)

        for user in leaderboard[0]['leaderboard']:
            if user['username'] == username:
                return (user['username'], np.float(user['logloss']['public']), user['rank']['public'], user['earned'], status_code)
        return (None, None, None, None, status_code)

    def login(self):
        r = requests.post(self._login_url, data=self.credentials)
        if r.status_code != 201:
            return (None, None, None, r.status_code)

        rj = r.json()
        return(rj['accessToken'], rj['refreshToken'], rj['id'], r.status_code)

    def authorize(self, file_path):
        accessToken, _, _, status_code = self.login()
        if status_code != 201:
            return (None, None, None, status_code)

        headers = {'Authorization': 'Bearer {0}'.format(accessToken)}

        r = requests.post(self._auth_url,
                          data={'filename': file_path.split('/')[-1], 'mimetype': 'text/csv'},
                          headers=headers)
        if r.status_code != 200:
            return (None, None, None, r.status_code)

        rj = r.json()
        return (rj['filename'], rj['signedRequest'], headers, r.status_code)

    def get_current_competition(self):
        now = datetime.now()
        leaderboard, status_code = self.get_leaderboard()
        if status_code != 200:
            return (None, None, None, None, status_code)

        for c in leaderboard:
            start_date = datetime.strptime(c['start_date'], '%Y-%m-%dT%H:%M:%S.%fZ')
            end_date = datetime.strptime(c['end_date'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if start_date < now < end_date:
                return (c['dataset_id'], c['_id'], status_code)

    def upload_prediction(self, file_path):
        filename, signedRequest, headers, status_code = self.authorize(file_path)
        if status_code != 200:
            return status_code

        dataset_id, _, status_code = self.get_current_competition()
        if status_code != 200:
            return status_code

        with open(file_path, 'rb') as fp:
            r = requests.Request('PUT', signedRequest, data=fp.read())
            prepped = r.prepare()
            s = requests.Session()
            resp = s.send(prepped)
            if resp.status_code != 200:
                return resp.status_code

        r = requests.post(self._submissions_url,
                          data={"dataset_id": dataset_id, "filename": filename},
                          headers=headers)

        return r.status_code
