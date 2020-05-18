# PylotonCycle
> Python Library for getting your Peloton workout data

## Table of contents
* [General info](#general-info)

## General info
As someone who wants to see my progress over time, I've been wanting a way
to pull and play with my ride data. However, I'm also cautious about linking
myself to too many external parties. As I've been playing with other libraries
out there, I wanted something that was a bit more intuitive and would play
nicer with the rest of my python code. So, PylotonCycle is born.

## Example Usage
```
import pylotoncycle

username = 'your username or email address'
password = 'your password'
conn = pylotoncycle.PylotonCycle(username, password)
workouts = conn.GetRecentWorkouts(5)
```

## TODO
* Lots more to cover. I want to find the right format for pulling in the
ride performance data.
