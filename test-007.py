import asyncio
from PerformanceTimer import PerformanceTimer
from utility import SuspendAlways

async def TestAsync():
	print("TestAsync-Enter")
	await SuspendAlways()
	print("After first await")
	await SuspendAlways()
	print("TestAsync-Leave")
	return 42

class CoroutineProxy:
	overallTimer = None
	stepCount = 0
	cpuDurationNs = 0

	def __init__(self, coro):
		self.coro = coro

	def __await__(self):
		self.overallTimer = PerformanceTimer(autoStart=True)
		while True:
			print("Proxy-About to step")
			stepTimer = PerformanceTimer(autoStart=True)
			stillExecuting, result = self.Step()
			stepTimer.Stop()
			print(f"Proxy-Step duration: {stepTimer}")
			self.stepCount += 1
			self.cpuDurationNs += stepTimer.GetDurationNs()
			if not stillExecuting:
				self.overallTimer.Stop()
				print(f"Proxy-Overall duration: {self.overallTimer}, steps {self.stepCount}, CPU duration: {self.cpuDurationNs}")
				return result
			yield

	def Step(self):
		try:
			self.coro.send(None)
			return True, None
		except StopIteration as exception:
			return False, exception.value

async def MainAsync():
	print("Main-Enter")
	print("Main-Creating TestAsync coroutine")
	coro = TestAsync()
	print("Main-Creating CoroutineProxy")
	proxy = CoroutineProxy(coro)
	print("Main-Awaiting proxy")
	result = await proxy
	print(f"Proxy result {result}")
	print("Main-Leave")

asyncio.run(MainAsync())

"""
Main-Enter
Main-Creating TestAsync coroutine
Main-Creating CoroutineProxy
Main-Awaiting proxy
Proxy-About to step
TestAsync-Enter
Proxy-Step duration: 40.40us
Proxy-About to step
After first await
Proxy-Step duration: 72.50us
Proxy-About to step
TestAsync-Leave
Proxy-Step duration: 20.40us
Proxy-Overall duration: 414.90us, steps 3, CPU duration: 133300
Proxy result 42
Main-Leave
"""
