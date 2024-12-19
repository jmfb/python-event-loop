import asyncio
import time
from AsyncWrapper import AsyncWrapper
from utility import SuspendMaybe

# Create a minimal CustomEventLoop implementation
class CustomEventLoop(asyncio.AbstractEventLoop):
	timers = []
	ready = []
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

	def create_task(self, coro, *, name=None, context=None):
		return asyncio.Task(
			coro,
			loop=self,
			name=name,
			context=context
		)

	def run_forever(self):
		asyncio._set_running_loop(self)
		self.isRunning = True
		while self.isRunning:
			self.run_once()
			# spinning hot on the CPU
		asyncio._set_running_loop(None)

	def GetWhen(self, delay):
		return time.monotonic() + delay

	def GetNow(self):
		return self.GetWhen(self.clockResolution)

	"""
	This run_once implementation current finds all expired timers and then runs
	them in the order they were added.  However, this FIFO behavior may not be
	the desired queuing algorithm.
	"""
	def run_once(self):
		now = self.GetNow()
		elapsed_timers = [timer for timer in self.timers if timer.when() < now]
		for timer in elapsed_timers:
			timer._scheduled = False
		self.timers = [timer for timer in self.timers if timer.when() >= now]
		# Order: Ready handles and then newly elpased timers?
		ready = self.ready + elapsed_timers
		self.ready = []
		for handle in ready:
			if not handle._cancelled:
				handle._run()

	def close(self):
		print("close")

	def get_debug(self):
		return False

	# Add a "ready" callback to the end of the "ready" list
	def call_soon(self, callback, *args, context=None):
		handle = asyncio.Handle(callback, args, loop=self, context=context)
		self.ready.append(handle)
		return handle

	def call_later(self, delay, callback, *args, context=None):
		return self.call_at(self.GetWhen(delay), callback, *args, context=context)

	# Store a timer to be checked in the run_once loop.  When it expires, the
	# callback will be called.
	def call_at(self, when, callback, *args, context=None):
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

async def TestAsync(index):
	print(f"TestAsync-Enter-{index}")
	for _ in range(3):
		await SuspendMaybe()
	print(f"TestAsync-Exit-{index}")

async def WrapperAsync(index):
	wrapper = AsyncWrapper(TestAsync(index))
	await wrapper.Wait()
	wrapper.Print()

async def MainAsync():
	print("MainAsync-Enter")
	tasks = [asyncio.create_task(WrapperAsync(index)) for index in range(5)]
	await asyncio.gather(*tasks)
	print("MainAsync-Exit")
	return 1

asyncio.run(MainAsync(), loop_factory=CustomEventLoop)

"""
MainAsync-Enter
TestAsync-Enter-0
TestAsync-Enter-1
TestAsync-Enter-2
TestAsync-Enter-3
TestAsync-Exit-3
Duration: 136.60us
TestAsync-Enter-4
TestAsync-Exit-2
Duration: 446.90us
TestAsync-Exit-1
Duration: 672.70us
TestAsync-Exit-0
Duration: 890.40us
TestAsync-Exit-4
Duration: 459.50us
MainAsync-Exit
close
"""
