import asyncio
import queue

def Step(task):
	try:
		task.get_coro().send(None)
		return True
	except StopIteration as exception:
		# Hack: Need to bypass the asyncio.Task.set_future override that
		# throws in order to set the asyncio.Future._result value.
		baseFuture: asyncio.Future = super(type(task), task)
		baseFuture.set_result(exception.value)
		return False

# Create a minimal CustomEventLoop implementation
class CustomEventLoop(asyncio.BaseEventLoop):
	def __init__(self):
		super().__init__()
		# Just use a queue of tasks
		self.tasks = queue.Queue()

	def run_forever(self):
		# WARNING: Poor implementation.
		# Loop through each task until it is done.
		# Note that if the task in question requires a different task this will
		# block forever.
		while not self.tasks.empty():
			task = self.tasks.get()
			# We need to call our custom coroutine step function because the
			# built-in asyncio.Task.__step function is private.
			while Step(task):
				print("Stepping")

	def create_task(self, coro, *, name = None, context = None):
		task = asyncio.Task(
			coro,
			loop=self,
			name=repr(name) if name is not None else None,
			context=context
		)
		self.tasks.put(task)
		return task

class SuspendAlways():
	def __await__(self):
		yield

async def MainAsync():
	print("MainAsync-Enter")
	await SuspendAlways()
	await SuspendAlways()
	print("MainAsync-Exit")
	return 1

loop = CustomEventLoop()
asyncio.set_event_loop(loop)
task = loop.create_task(MainAsync())
loop.run_forever()
print(f"Main result = {task.result()}")
