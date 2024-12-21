import asyncio
import time
from PerformanceTimer import PerformanceTimer
from utility import SuspendAlways

class CoroutineProxy:
	overallTimer = None
	stepCount = 0
	cpuDurationNs = 0

	def __init__(self, coro):
		self.coro = coro

	def __await__(self):
		self.overallTimer = PerformanceTimer(autoStart=True)
		while True:
			stepTimer = PerformanceTimer(autoStart=True)
			print("begin-step")
			stillExecuting, result = self.Step()
			print("end-step")
			stepTimer.Stop()
			self.stepCount += 1
			self.cpuDurationNs += stepTimer.GetDurationNs()
			if not stillExecuting:
				self.overallTimer.Stop()
				return result
			yield

	def Step(self):
		try:
			self.coro.send(None)
			return True, None
		except StopIteration as exception:
			return False, exception.value

class CustomEventLoop(asyncio.AbstractEventLoop):
	timers = []
	isRunning = False
	clockResolution = time.get_clock_info('monotonic').resolution

	def stop(self):
		self.isRunning = False

	def run_until_complete(self, future):
		if not asyncio.isfuture(future):
			future = asyncio.ensure_future(future, loop=self)
		future.add_done_callback(lambda future: future.get_loop().stop())
		self.run_forever()
		return future.result()


	async def create_proxy(self, coro):
		return await CoroutineProxy(coro)

	def create_task(self, coro, *, name=None, context=None):
		proxy = self.create_proxy(coro)
		print("create_task-before")
		task = asyncio.Task(
			proxy,
			loop=self,
			name=name,
			context=context
		)
		print("create_task-after")
		return task

	def run_forever(self):
		asyncio._set_running_loop(self)
		self.isRunning = True
		while self.isRunning:
			self.run_once()
		asyncio._set_running_loop(None)

	def GetWhen(self, delay):
		return time.monotonic() + delay

	def GetNow(self):
		return self.GetWhen(self.clockResolution)

	def run_once(self):
		now = self.GetNow()
		elapsed_timers = [timer for timer in self.timers if timer.when() < now]
		for timer in elapsed_timers:
			timer._scheduled = False
		self.timers = [timer for timer in self.timers if timer.when() >= now]
		for handle in elapsed_timers:
			if not handle._cancelled:
				print("handle_run-before")
				handle._run()
				print("handle_run-after")

	def close(self):
		print("close")

	def get_debug(self):
		return False

	def call_soon(self, callback, *args, context=None):
		return self.call_later(0, callback, *args, context=context)

	def call_later(self, delay, callback, *args, context=None):
		return self.call_at(self.GetWhen(delay), callback, *args, context=context)

	def call_at(self, when, callback, *args, context=None):
		print("call_at")
		timer = asyncio.TimerHandle(when, callback, args, loop=self, context=context)
		self.timers.append(timer)
		timer._scheduled = True
		return timer

	def call_exception_handler(self, context):
		print(context)

	def create_future(self):
		return asyncio.Future(loop=self)

	async def shutdown_asyncgens(self):
		pass

	async def shutdown_default_executor(self, timeout=None):
		pass

	def _timer_handle_cancelled(self, handle):
		pass

async def TestAsync():
	print(f"TestAsync-Enter")
	await SuspendAlways()
	print(f"TestAsync-Middle")
	await SuspendAlways()
	print(f"TestAsync-Exit")

async def MainAsync():
	print("MainAsync-Enter")
	await TestAsync()
	print("MainAsync-Exit")
	return 1

asyncio.run(MainAsync(), loop_factory=CustomEventLoop)

"""
The initial task is create from within the call to run wrapping our MainAsync
coroutine with a task.  This would be a top level task.  Because the call to
call_at occurs _while_ the task is being created, we can associate the call_at
handle with the "being created" task metadata.

>> create_task-before
>> call_at
>> create_task-after

We know the handle being executed is being "billed" to the top level task
created from the previous step.  The continuation registered with the call_at
here can be billed back to the original top level task.

>> handle_run-before
>> begin-step
>> MainAsync-Enter
>> TestAsync-Enter
>> end-step
>> call_at
>> handle_run-after

This is the first continuation of the top level task.  It has a further
continuation at the call_at that can be billed back to the original task.

>> handle_run-before
>> begin-step
>> TestAsync-Middle
>> end-step
>> call_at
>> handle_run-after

This is the final branch of the top level task, but still creates one more
continuation (implementation details of asyncio?).

>> handle_run-before
>> begin-step
>> TestAsync-Exit
>> MainAsync-Exit
>> end-step
>> call_at
>> handle_run-after

This is the final-final branch (none of the code from the original task is
being executed at this point, it must just be some "task" cleanup code).  We
would bill this back to the original task.  Because there are no more pending
continuations for the original task - this would conclude the timing metrics
for the top level task.

>> handle_run-before
>> handle_run-after

I have no clue what task this is.  This must be some kind of asyncio inner
working task to cleanup.  This would constitute a new top-level task for logging
purposes but as far as reporting it back out, we would not be able to tie it to
any originating functionality (like our MainAsync call).  Perhaps just log is as
overhead.

>> create_task-before
>> call_at
>> create_task-after

With its first continuation (not done yet).

>> handle_run-before
>> begin-step
>> end-step
>> call_at
>> handle_run-after

And second continuation (now it is done).

>> handle_run-before
>> handle_run-after

And a second unknown task is created.

>> create_task-before
>> call_at
>> create_task-after

With its first continuation (not done yet).

>> handle_run-before
>> begin-step
>> end-step
>> call_at
>> handle_run-after

And second continuation (now it is done).

>> handle_run-before
>> handle_run-after

And finally, the top level asyncio.run call is completed and the loop is closed.

>> close
"""
