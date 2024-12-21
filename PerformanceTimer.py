import time

class PerformanceTimer:
	isRunning = False
	start = None
	end = None

	def __init__(self, autoStart=True):
		if autoStart:
			self.Start()

	def GetNowNs(self):
		return time.perf_counter_ns()

	def Start(self):
		if self.isRunning:
			raise RuntimeError("Timer is already running")
		self.isRunning = True
		self.start = self.GetNowNs()

	def Stop(self):
		if not self.isRunning:
			raise RuntimeError("Timer is not running")
		self.isRunning = False
		self.end = self.GetNowNs()

	def GetDurationNs(self):
		if self.start is None:
			raise RuntimeError("Timer was never started")
		end = self.GetNowNs() if self.end is None or self.isRunning else self.end
		return end - self.start

	def __repr__(self):
		if self.start is None:
			return "Timer not started"
		durationNs = self.GetDurationNs()
		if durationNs < 1000:
			return f"{durationNs}ns"
		durationUs = durationNs / 1000
		if durationUs < 1000:
			return f"{durationUs:.2f}us"
		durationMs = durationUs / 1000
		if durationMs < 1000:
			return f"{durationMs:.2f}ms"
		durationS = durationMs / 1000
		return f"{durationS:.2f}s"
