# endpoint info derived from
# https://github.com/philosowaffle/postman_collections/blob/master/PelotonCycle/

# https://app.swaggerhub.com/apis/DovOps/peloton-unofficial-api/0.2.3

# import pprint
import requests


class PelotonLoginException(Exception):
    pass


class PylotonCycle:
    def __init__(self, username, password):
        self.base_url = 'https://api.onepeloton.com'
        self.s = requests.Session()
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'pylotoncycle'
        }

        # Initialize a couple of variables that will get reused
        # userid - our userid
        # instructor_id_dict - dictionary that will allow us to cache
        #                      information
        #                      format is: instructor_id : instructor_dict
        self.userid = None
        self.instructor_id_dict = {}

        self.login(username, password)

    def login(self, username, password):
        auth_login_url = '%s/auth/login' % self.base_url
        auth_payload = {
            'username_or_email': username,
            'password': password
        }
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'pyloton'
        }
        resp = self.s.post(
            auth_login_url,
            json=auth_payload, headers=headers, timeout=10).json()

        if (('status' in resp) and (resp['status'] == 401)):
            raise PelotonLoginException(resp['message'] if ('message' in resp)
                  else "Login Failed")

        self.userid = resp['user_id']

    def GetMe(self):
        url = '%s/api/me' % self.base_url
        resp = self.s.get(url, timeout=10).json()
        self.username = resp['username']
        self.userid = resp['id']
        self.total_workouts = resp['total_workouts']
        return resp

    def GetUrl(self, url):
        resp = self.s.get(url, timeout=10).json()
        return resp

    def GetWorkoutList(self, num_workouts=None):
        '''
        Generally, not intended to call this directly, but
        rather through a helper function.
        num_workouts - specify the X most recent workouts to fetch. If left
                       as None, it will fetch all the workouts
        '''
        if num_workouts is None:
            self.GetMe()
            num_workouts = self.total_workouts

        limit = 100
        pages = num_workouts // limit
        rem = num_workouts % limit

        base_workout_url = \
            '%s/api/user/%s/workouts?sort_by=-created' % (
                self.base_url, self.userid)

        workout_list = []
        current_page = 0

        while current_page < pages:
            url = '%s&page=%s&limit=%s' % (
                base_workout_url, current_page, limit)
            resp = self.s.get(url, timeout=10).json()
            workout_list.extend(resp['data'])
            current_page += 1

        # if we have a remainder to fetch, then do another
        # call and extend on only that numbder of results
        if rem != 0:
            url = '%s&page=%s&limit=%s' % (
                base_workout_url, current_page, limit)
            resp = self.s.get(url, timeout=10).json()
            workout_list.extend(resp['data'][0:rem])

        return workout_list

    def GetRecentWorkouts(self, num_workouts=None):
        workout_list = self.GetWorkoutList(num_workouts)
        workouts_info = []

        for i in workout_list:
            workout_id = i['id']

            resp_summary = self.GetWorkoutSummaryById(workout_id)
            resp_workout = self.GetWorkoutById(workout_id)

            if 'instructor_id' in resp_workout['ride']:
                instructor_id = resp_workout['ride']['instructor_id']
                resp_instructor = self.GetInstructorById(instructor_id)
            elif 'instructor' in resp_workout['ride']:
                resp_instructor = {
                    'name': resp_workout['ride']['instructor']['name']
                }

            resp_workout['overall_summary'] = resp_summary
            try:
                resp_workout['instructor_name'] = resp_instructor['name']
            except KeyError:
                resp_workout['instructor_name'] = None
            workouts_info.append(resp_workout)
        return workouts_info

    def GetWorkoutSummaryById(self, workout_id):
        url = '%s/api/workout/%s' % (self.base_url, workout_id)
        resp = self.GetUrl(url)
        return resp

    def GetWorkoutMetricsById(self, workout_id, frequency=50):
        url = '%s/api/workout/%s/performance_graph?every_n=%s' % (
            self.base_url, workout_id, frequency)
        resp = self.GetUrl(url)
        return resp

    def GetWorkoutById(self, workout_id):
        url = '%s/api/workout/%s' % (self.base_url, workout_id)
        resp = self.GetUrl(url)
        return resp

    def GetInstructorById(self, instructor_id):
        if instructor_id in self.instructor_id_dict:
            return self.instructor_id_dict[instructor_id]

        url = '%s/api/instructor/%s' % (self.base_url, instructor_id)
        resp = self.GetUrl(url)
        self.instructor_id_dict[instructor_id] = resp
        return resp

    def GetFollowersById(self, userid=None):
        if userid is None:
            userid = self.userid
        url = '%s/api/user/%s/followers' % (self.base_url, userid)
        resp = self.GetUrl(url)
        return resp

    def ParseMetricsData(self, metrics_data):
        # TODO
        pass


if __name__ == '__main__':
    username = 'My_Peloton_User_or_Email'
    password = 'My_Peloton_Password'
    conn = PylotonCycle(username, password)
