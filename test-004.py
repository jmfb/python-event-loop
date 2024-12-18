import asyncio

class DummySelector:
	def select(self, timeout):
		pass

# A bare-bones CustomEventLoop (just needed _selector and _process_events)
# The rest of the overrides are just for inspection.
class CustomEventLoop(asyncio.BaseEventLoop):
	def __init__(self):
		print("CustomEventLoop.__init__")
		super().__init__()
		# This is required by the default run_forever implementation
		self._selector = DummySelector()

	def run_forever(self):
		print("CustomEventLoop.run_forever")
		super().run_forever()

	def _run_once(self):
		print("CustomEventLoop._run_once")
		super()._run_once()

	def create_task(self, coro, *, name = None, context = None):
		print("CustomEventLoop.CreateTask")
		return super().create_task(coro, name=name, context=context)

	# This is required by the default run_forever implementation
	def _process_events(self, events):
		pass

class SuspendAlways():
	def __await__(self):
		yield

async def MainAsync():
	print("MainAsync-Enter")
	await SuspendAlways()
	await asyncio.sleep(10)
	print("MainAsync-Exit")
	return 1

# Use the library "run" method with our custom event loop
asyncio.run(
	MainAsync(),
	loop_factory=CustomEventLoop
)

"""
CustomEventLoop.__init__
CustomEventLoop.CreateTask
CustomEventLoop.run_forever
CustomEventLoop._run_once
MainAsync-Enter
CustomEventLoop._run_once
... (many calls, CPU sits around 2% while polling) ...
CustomEventLoop._run_once
MainAsync-Exit
CustomEventLoop._run_once
CustomEventLoop.CreateTask
CustomEventLoop.run_forever
CustomEventLoop._run_once
CustomEventLoop._run_once
CustomEventLoop.CreateTask
CustomEventLoop.run_forever
CustomEventLoop._run_once
CustomEventLoop._run_once
"""
