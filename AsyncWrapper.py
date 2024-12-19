from PerformanceTimer import PerformanceTimer

class AsyncWrapper:
	def __init__(self, awaitable):
		self.timer = PerformanceTimer(autoStart=True)
		self.awaitable = awaitable

	async def Wait(self):
		await self.awaitable
		self.timer.Stop()

	def Print(self):
		print(f"Duration: {repr(self.timer)}")
