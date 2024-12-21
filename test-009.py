import asyncio
import time
from utility import SuspendAlways

class IdleMetrics:
	__slots__ = ('startedAt', 'finishedAt')

	def __init__(self):
		self.startedAt = time.perf_counter_ns()

	def Finish(self):
		self.finishedAt = time.perf_counter_ns()

	def Print(self):
		print(f"idle from {self.startedAt} to {self.finishedAt}")

class StepMetrics:
	__slots__ = (
		'stepId',
		'createdAt',
		'startedAt',
		'finishedAt'
	)

	def __init__(self, stepId):
		self.stepId = stepId
		self.createdAt = time.perf_counter_ns()
		self.startedAt = None
		self.finishedAt = None

	def Start(self):
		self.startedAt = time.perf_counter_ns()

	def Finish(self):
		self.finishedAt = time.perf_counter_ns()

	def Print(self):
		print(f"  stepId={self.stepId}, " \
			f"createdAt={self.createdAt}, " \
			f"startedAt={self.startedAt}, " \
			f"finishedAt={self.finishedAt}")

class TaskMetrics:
	__slots__ = (
		'parentTaskId',
		'taskId',
		'createdAt',
		'nextStepId',
		'steps'
	)

	def __init__(self, parentTaskId, taskId):
		self.parentTaskId = parentTaskId
		self.taskId = taskId
		self.createdAt = time.perf_counter_ns()
		self.nextStepId = 0
		self.steps = []

	def CreateStep(self):
		stepId = self.nextStepId
		self.nextStepId += 1
		self.steps.append(StepMetrics(stepId))
		return stepId

	def Print(self):
		print(f"taskId={self.taskId}, " \
			f"parent={self.parentTaskId}, " \
			f"createdAt={self.createdAt}")
		for step in self.steps:
			step.Print()

class StepHandle(asyncio.TimerHandle):
	__slots__ = ('taskId', 'stepId')

	def __init__(self, taskId, stepId, when, callback, *args, loop, context):
		self.taskId = taskId
		self.stepId = stepId
		super().__init__(when, callback, *args, loop=loop, context=context)

class CustomEventLoop(asyncio.AbstractEventLoop):
	__slots__ = (
		'timers',
		'isRunning',
		'clockResolution',
		'nextTaskId',
		'currentTaskId',
		'tasks',
		'currentIdle',
		'idles'
	)

	def __init__(self):
		super().__init__()
		self.timers = []
		self.isRunning = False
		self.clockResolution = time.get_clock_info('monotonic').resolution
		self.nextTaskId = 0
		self.currentTaskId = None
		self.tasks = []
		self.currentIdle = None
		self.idles = []

	def FinishIdle(self):
		idle = self.currentIdle
		if idle is None:
			return
		self.currentIdle = None
		idle.Finish()
		self.idles.append(idle)

	def StartIdle(self):
		if self.currentIdle is None:
			self.currentIdle = IdleMetrics()

	def stop(self):
		self.FinishIdle()
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
		parentTaskId = self.currentTaskId
		taskId = self.nextTaskId
		self.nextTaskId += 1
		self.tasks.append(TaskMetrics(parentTaskId, taskId))

		self.currentTaskId = taskId
		task = asyncio.Task(
			coro,
			loop=self,
			name=name,
			context=context
		)
		self.currentTaskId = parentTaskId

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
		if not elapsed_timers:
			self.StartIdle()
		else:
			self.FinishIdle()
			for handle in elapsed_timers:
				if not handle._cancelled:
					parentTaskId = self.currentTaskId
					self.currentTaskId = handle.taskId
					step = self.tasks[handle.taskId].steps[handle.stepId]
					step.Start()
					handle._run()
					step.Finish()
					self.currentTaskId = parentTaskId

	def close(self):
		for task in self.tasks:
			task.Print()
		if not self.idles:
			print("Loop was never idle")
		else:
			for idle in self.idles:
				idle.Print()

	def get_debug(self):
		return False

	def call_soon(self, callback, *args, context=None):
		return self.call_later(0, callback, *args, context=context)

	def call_later(self, delay, callback, *args, context=None):
		return self.call_at(self.GetWhen(delay), callback, *args, context=context)

	def call_at(self, when, callback, *args, context=None):
		taskId = self.currentTaskId
		if taskId is None:
			raise RuntimeError("call_at could not be tracked back to a task ID")
		stepId = self.tasks[taskId].CreateStep()
		timer = StepHandle(
			taskId,
			stepId,
			when,
			callback,
			args,
			loop=self,
			context=context
		)
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

async def GrandchildAsync():
	await SuspendAlways()

async def ChildAsync():
	await asyncio.create_task(GrandchildAsync())

async def MainAsync():
	await SuspendAlways()
	sleep = asyncio.sleep(1)
	task = asyncio.create_task(ChildAsync())
	await asyncio.gather(sleep, task)

asyncio.run(MainAsync(), loop_factory=CustomEventLoop)

"""
taskId=0, parent=None, createdAt=532236061980400
  stepId=0, createdAt=532236061987700, startedAt=532236062007500, finishedAt=532236062020700
  stepId=1, createdAt=532236062017500, startedAt=532236062022900, finishedAt=532236062042700
taskId=1, parent=0, createdAt=532236062025200
  stepId=0, createdAt=532236062027000, startedAt=532236062044300, finishedAt=532236062050600
taskId=2, parent=0, createdAt=532236062032300
  stepId=0, createdAt=532236062033600, startedAt=532236062050800, finishedAt=532236062056300
  stepId=1, createdAt=532236062053000, startedAt=532237057464000, finishedAt=532237057484300
  stepId=2, createdAt=532237057476100, startedAt=532237057485400, finishedAt=532237057505500
  stepId=3, createdAt=532237057499900, startedAt=532237057506800, finishedAt=532237057514200
  stepId=4, createdAt=532237057512400, startedAt=532237057515600, finishedAt=532237057520100
  stepId=5, createdAt=532237057518900, startedAt=532237057526200, finishedAt=532237057527700
taskId=3, parent=1, createdAt=532236062045400
  stepId=0, createdAt=532236062046900, startedAt=532236062057400, finishedAt=532236062060400
  stepId=1, createdAt=532236062058900, startedAt=532236062061200, finishedAt=532236062064300
  stepId=2, createdAt=532236062062700, startedAt=532236062065000, finishedAt=532236062069200
  stepId=3, createdAt=532236062068100, startedAt=532236062073600, finishedAt=532236062074500
taskId=4, parent=None, createdAt=532237057574400
  stepId=0, createdAt=532237057577900, startedAt=532237057583200, finishedAt=532237057587000
  stepId=1, createdAt=532237057585300, startedAt=532237057588000, finishedAt=532237057588800
taskId=5, parent=None, createdAt=532237057592600
  stepId=0, createdAt=532237057593900, startedAt=532237057596300, finishedAt=532237057599700
  stepId=1, createdAt=532237057598500, startedAt=532237057600300, finishedAt=532237057600700
idle from 532236062075500 to 532237057461100
"""
