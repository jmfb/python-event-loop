import asyncio
import time

# Create a minimal CustomEventLoop implementation
class CustomEventLoop(asyncio.AbstractEventLoop):
	def __init__(self):
		self.timers = []
		self.isRunning = False

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

	def _GetNow(self):
		return time.monotonic() + time.get_clock_info('monotonic').resolution

	def run_once(self):
		now = self._GetNow()
		elapsed_timers = [timer for timer in self.timers if timer.when() < now]
		self.timers = [timer for timer in self.timers if timer.when() >= now]
		for timer in elapsed_timers:
			timer._scheduled = False
			if not timer._cancelled:
				print("...step")
				timer._run()

	def close(self):
		print("close")

	def get_debug(self):
		return False

	def call_later(self, delay, callback, *args, context=None):
		return self.call_at(time.monotonic() + delay, callback, *args, context=context)

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

class SuspendAlways():
	def __await__(self):
		yield

async def MainAsync():
	print("MainAsync-Enter")
	await SuspendAlways()
	await asyncio.sleep(1)
	print("MainAsync-Exit")
	return 1

asyncio.run(MainAsync(), loop_factory=CustomEventLoop)
