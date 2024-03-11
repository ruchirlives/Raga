# Play the Raga Bhairav
from bhairav import raga_bhairav as raga
import simpy
import random


class scheduledevent:
    def __init__(self, name, time, mood):
        self.name = name
        self.time = time
        self.mood = mood


class conductor:
    def __init__(self, env, schedule):
        self.env = env
        self.players = []
        self.implementschedule(schedule)
        self.timer = env.process(self.timer())

    def implementschedule(self, schedule):
        for item in schedule:
            event = env.event()
            event.name = item.name
            event.time = item.time
            event.mood = item.mood
            env.process(self.scheduleevent(event))

    def scheduleevent(self, event):
        yield env.timeout(event.time)
        print("Event triggered", event.name)
        self.notify(event)

    def addplayer(self, player):
        self.players.append(player)

    def notify(self, event):
        print("notifying", event.mood)
        for player in self.players:
            if event.name in player.participation:
                player.mood = event.mood
            else:
                player.mood = None  # no mood to play

    def begin(self):
        yield env.timeout(0)
        raga.mmcmidi()
        for player in self.players:
            self.env.process(player.play_raga())

    def timer(self):
        env = self.env
        while 1:
            print("Time", env.now)
            yield env.timeout(1)


class Player:
    def __init__(self, env, name="player", rules={}, participation=[]):
        self.env = env
        self.name = name
        self.mood = None
        self.rules = rules
        self.participation = participation

    # 		raga["base_duration_rule"]=lambda x: 0.5

    def play_raga(self):
        while 1:
            if not self.mood:
                nextbeat = round(env.now + 0.5)
                wait = nextbeat - env.now if (nextbeat - env.now) > 0 else 1
                yield self.env.timeout(wait)  # Wait a beat before checking again
                continue
            self.checkmood()
            lengthinsecs = raga.play()
            secondsperbeat = 60 / raga.bpm
            lengthinbeats = lengthinsecs / secondsperbeat

            print(
                f"Playing {self.name} at time {self.env.now} for {lengthinbeats} with {self.mood} mood."
            )
            yield self.env.timeout(
                lengthinbeats
            )  # Simulate the time taken to play the raga

        return

    def checkmood(self):
        mood = self.mood
        rules = self.rules
        if mood in self.rules:
            rules = self.rules[mood]
            for rule_key, rule_value in rules.items():
                raga.rules[rule_key] = rule_value

        return


# SimPy Environment
beat = 60 / raga.bpm
env = simpy.rt.RealtimeEnvironment(factor=beat, strict=True)

schedule = [
    scheduledevent("alaap", 0, "slow"),
    scheduledevent("elaboration", 30, "developing"),
    scheduledevent("development", 60, "paced"),
]

conductor = conductor(env, schedule)

# Usage
participation = ["alaap", "elaboration", "development"]
rules = {
    "slow": {
        "base_duration_rule": lambda x: 1.5 * beat,
        "phrase_velocity_rule": lambda x: random.randint(0, 50),
    },
    "developing": {
        "base_duration_rule": lambda x: 1.0 * beat,
        "phrase_velocity_rule": lambda x: random.randint(50, 70),
    },
    "paced": {
        "base_duration_rule": lambda x: 0.5 * beat,
        "phrase_velocity_rule": lambda x: random.randint(70, 127),
    },
}
player = Player(env, name="Sitarist", participation=participation, rules=rules)
conductor.addplayer(player)
env.process(conductor.begin())

# Run the simulation
env.run(until=80)
