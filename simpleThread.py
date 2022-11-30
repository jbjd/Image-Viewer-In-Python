# edited version from python source
import sys
from _thread import _excepthook as excepthook, _ExceptHookArgs as ExceptHookArgs, get_ident, allocate_lock, start_new_thread, _set_sentinel
from time import monotonic as _time
from collections import deque

# classes used by thread
class Condition:
	"""Class that implements a condition variable.
	A condition variable allows one or more threads to wait until they are
	notified by another thread.
	If the lock argument is given and not None, it must be a Lock or RLock
	object, and it is used as the underlying lock. Otherwise, a new RLock object
	is created and used as the underlying lock.
	"""

	def __init__(self, lock=None):
		if lock is None:
			lock = RLock()
		self._lock = lock
		# Export the lock's acquire() and release() methods
		self.acquire = lock.acquire
		self.release = lock.release
		# If the lock defines _release_save() and/or _acquire_restore(),
		# these override the default implementations (which just call
		# release() and acquire() on the lock).  Ditto for _is_owned().
		if hasattr(lock, '_release_save'):
			self._release_save = lock._release_save
		if hasattr(lock, '_acquire_restore'):
			self._acquire_restore = lock._acquire_restore
		if hasattr(lock, '_is_owned'):
			self._is_owned = lock._is_owned
		self._waiters = deque()

	def _at_fork_reinit(self):
		self._lock._at_fork_reinit()
		self._waiters.clear()

	def __enter__(self):
		return self._lock.__enter__()

	def __exit__(self, *args):
		return self._lock.__exit__(*args)

	def _release_save(self):
		self._lock.release()           # No state to save

	def _acquire_restore(self, x):
		self._lock.acquire()           # Ignore saved state

	def _is_owned(self):
		# Return True if lock is owned by current_thread.
		# This method is called only if _lock doesn't have _is_owned().
		if self._lock.acquire(False):
			self._lock.release()
			return False
		return True

	def wait(self, timeout=None):
		"""Wait until notified or until a timeout occurs.
		If the calling thread has not acquired the lock when this method is
		called, a RuntimeError is raised.
		This method releases the underlying lock, and then blocks until it is
		awakened by a notify() or notify_all() call for the same condition
		variable in another thread, or until the optional timeout occurs. Once
		awakened or timed out, it re-acquires the lock and returns.
		When the timeout argument is present and not None, it should be a
		floating point number specifying a timeout for the operation in seconds
		(or fractions thereof).
		When the underlying lock is an RLock, it is not released using its
		release() method, since this may not actually unlock the lock when it
		was acquired multiple times recursively. Instead, an internal interface
		of the RLock class is used, which really unlocks it even when it has
		been recursively acquired several times. Another internal interface is
		then used to restore the recursion level when the lock is reacquired.
		"""
		if not self._is_owned():
			raise RuntimeError("cannot wait on un-acquired lock")
		waiter = allocate_lock()
		waiter.acquire()
		self._waiters.append(waiter)
		saved_state = self._release_save()
		gotit = False
		try:    # restore state no matter what (e.g., KeyboardInterrupt)
			if timeout is None:
				waiter.acquire()
				gotit = True
			else:
				if timeout > 0:
					gotit = waiter.acquire(True, timeout)
				else:
					gotit = waiter.acquire(False)
			return gotit
		finally:
			self._acquire_restore(saved_state)
			if not gotit:
				try:
					self._waiters.remove(waiter)
				except ValueError:
					pass

	def wait_for(self, predicate, timeout=None):
		"""Wait until a condition evaluates to True.
		predicate should be a callable which result will be interpreted as a
		boolean value.  A timeout may be provided giving the maximum time to
		wait.
		"""
		endtime = None
		waittime = timeout
		result = predicate()
		while not result:
			if waittime is not None:
				if endtime is None:
					endtime = _time() + waittime
				else:
					waittime = endtime - _time()
					if waittime <= 0:
						break
			self.wait(waittime)
			result = predicate()
		return result

	def notify(self, n=1):
		"""Wake up one or more threads waiting on this condition, if any.
		If the calling thread has not acquired the lock when this method is
		called, a RuntimeError is raised.
		This method wakes up at most n of the threads waiting for the condition
		variable; it is a no-op if no threads are waiting.
		"""
		if not self._is_owned():
			raise RuntimeError("cannot notify on un-acquired lock")
		waiters = self._waiters
		while waiters and n > 0:
			waiter = waiters[0]
			try:
				waiter.release()
			except RuntimeError:
				# gh-92530: The previous call of notify() released the lock,
				# but was interrupted before removing it from the queue.
				# It can happen if a signal handler raises an exception,
				# like CTRL+C which raises KeyboardInterrupt.
				pass
			else:
				n -= 1
			try:
				waiters.remove(waiter)
			except ValueError:
				pass

	def notify_all(self):
		"""Wake up all threads waiting on this condition.
		If the calling thread has not acquired the lock when this method
		is called, a RuntimeError is raised.
		"""
		self.notify(len(self._waiters))

class RLock:
	"""This class implements reentrant lock objects.
	A reentrant lock must be released by the thread that acquired it. Once a
	thread has acquired a reentrant lock, the same thread may acquire it
	again without blocking; the thread must release it once for each time it
	has acquired it.
	"""

	def __init__(self):
		self._block = allocate_lock()
		self._owner = None
		self._count = 0

	def __repr__(self):
		owner = self._owner
		try:
			owner = _active[owner].name
		except KeyError:
			pass
		return "<%s %s.%s object owner=%r count=%d at %s>" % (
			"locked" if self._block.locked() else "unlocked",
			self.__class__.__module__,
			self.__class__.__qualname__,
			owner,
			self._count,
			hex(id(self))
		)

	def _at_fork_reinit(self):
		self._block._at_fork_reinit()
		self._owner = None
		self._count = 0

	def acquire(self, blocking=True, timeout=-1):
		"""Acquire a lock, blocking or non-blocking.
		When invoked without arguments: if this thread already owns the lock,
		increment the recursion level by one, and return immediately. Otherwise,
		if another thread owns the lock, block until the lock is unlocked. Once
		the lock is unlocked (not owned by any thread), then grab ownership, set
		the recursion level to one, and return. If more than one thread is
		blocked waiting until the lock is unlocked, only one at a time will be
		able to grab ownership of the lock. There is no return value in this
		case.
		When invoked with the blocking argument set to true, do the same thing
		as when called without arguments, and return true.
		When invoked with the blocking argument set to false, do not block. If a
		call without an argument would block, return false immediately;
		otherwise, do the same thing as when called without arguments, and
		return true.
		When invoked with the floating-point timeout argument set to a positive
		value, block for at most the number of seconds specified by timeout
		and as long as the lock cannot be acquired.  Return true if the lock has
		been acquired, false if the timeout has elapsed.
		"""
		me = get_ident()
		if self._owner == me:
			self._count += 1
			return 1
		rc = self._block.acquire(blocking, timeout)
		if rc:
			self._owner = me
			self._count = 1
		return rc

	__enter__ = acquire

	def release(self):
		"""Release a lock, decrementing the recursion level.
		If after the decrement it is zero, reset the lock to unlocked (not owned
		by any thread), and if any other threads are blocked waiting for the
		lock to become unlocked, allow exactly one of them to proceed. If after
		the decrement the recursion level is still nonzero, the lock remains
		locked and owned by the calling thread.
		Only call this method when the calling thread owns the lock. A
		RuntimeError is raised if this method is called when the lock is
		unlocked.
		There is no return value.
		"""
		if self._owner != get_ident():
			raise RuntimeError("cannot release un-acquired lock")
		self._count = count = self._count - 1
		if not count:
			self._owner = None
			self._block.release()

	def __exit__(self, t, v, tb):
		self.release()

	# Internal methods used by condition variables

	def _acquire_restore(self, state):
		self._block.acquire()
		self._count, self._owner = state

	def _release_save(self):
		if self._count == 0:
			raise RuntimeError("cannot release un-acquired lock")
		count = self._count
		self._count = 0
		owner = self._owner
		self._owner = None
		self._block.release()
		return (count, owner)

	def _is_owned(self):
		return self._owner == get_ident()

class Event:
	"""Class implementing event objects.
	Events manage a flag that can be set to true with the set() method and reset
	to false with the clear() method. The wait() method blocks until the flag is
	true.  The flag is initially false.
	"""

	def __init__(self):
		self._cond = Condition(allocate_lock())
		self._flag = False

	def _at_fork_reinit(self):
		# Private method called by Thread._reset_internal_locks()
		self._cond._at_fork_reinit()

	def is_set(self):
		"""Return true if and only if the internal flag is true."""
		return self._flag

	def set(self):
		"""Set the internal flag to true.
		All threads waiting for it to become true are awakened. Threads
		that call wait() once the flag is true will not block at all.
		"""
		with self._cond:
			self._flag = True
			self._cond.notify_all()

	def clear(self):
		"""Reset the internal flag to false.
		Subsequently, threads calling wait() will block until set() is called to
		set the internal flag to true again.
		"""
		with self._cond:
			self._flag = False

	def wait(self, timeout=None):
		"""Block until the internal flag is true.
		If the internal flag is true on entry, return immediately. Otherwise,
		block until another thread calls set() to set the flag to true, or until
		the optional timeout occurs.
		When the timeout argument is present and not None, it should be a
		floating point number specifying a timeout for the operation in seconds
		(or fractions thereof).
		This method returns the internal flag on exit, so it will always return
		True except if a timeout is given and the operation times out.
		"""
		with self._cond:
			signaled = self._flag
			if not signaled:
				signaled = self._cond.wait(timeout)
			return signaled

# globals
threadCount = 0 # incremented for each new thread
_active = {}    # maps thread id to Thread object
_active_limbo_lock = RLock()
_limbo = {}
_shutdown_locks_lock = allocate_lock()
_shutdown_locks = set()

class Thread:

	_initialized = False

	def __init__(self, target=None, name=None,
				args=(), kwargs=None, *, daemon=None):
		"""This constructor should always be called with keyword arguments. Arguments are:
		*group* should be None; reserved for future extension when a ThreadGroup
		class is implemented.
		*target* is the callable object to be invoked by the run()
		method. Defaults to None, meaning nothing is called.
		*name* is the thread name. By default, a unique name is constructed of
		the form "Thread-N" where N is a small decimal number.
		*args* is a list or tuple of arguments for the target invocation. Defaults to ().
		*kwargs* is a dictionary of keyword arguments for the target
		invocation. Defaults to {}.
		If a subclass overrides the constructor, it must make sure to invoke
		the base class constructor (Thread.__init__()) before doing anything
		else to the thread.
		"""
		if kwargs is None:
			kwargs = {}
		if name:
			name = str(name)
		else:
			global threadCount
			name = f"Thread-{threadCount}"
			threadCount += 1
			if target is not None:
				try:
					target_name = target.__name__
					name += f" ({target_name})"
				except AttributeError:
					pass

		self._target = target
		self._name = name
		self._args = args
		self._kwargs = kwargs
		self._daemonic = daemon if daemon is not None else current_thread().daemon
		self._tstate_lock = self._ident = None
		self._started = Event()
		self._is_stopped = False
		self._initialized = True
		# Copy of sys.stderr used by self._invoke_excepthook()
		self._stderr = sys.stderr
		self._invoke_excepthook = _make_invoke_excepthook()

	def _reset_internal_locks(self, is_alive):
		# private!  Called by _after_fork() to reset our internal locks as
		# they may be in an invalid state leading to a deadlock or crash.
		self._started._at_fork_reinit()
		if is_alive and self._tstate_lock is not None:
			self._tstate_lock._at_fork_reinit()
			self._tstate_lock.acquire()
		else:
			# The thread isn't alive after fork: it doesn't have a tstate anymore.
			self._is_stopped = True
			self._tstate_lock = None

	def __repr__(self):
		status = "initial"
		if self._started.is_set():
			status = "started"
		self.is_alive() # easy way to get ._is_stopped set when appropriate
		if self._is_stopped:
			status = "stopped"
		if self._daemonic:
			status += " daemon"
		if self._ident is not None:
			status += " %s" % self._ident
		return "<%s(%s, %s)>" % (self.__class__.__name__, self._name, status)

	def start(self):
		"""Start the thread's activity.
		It must be called at most once per thread object. It arranges for the
		object's run() method to be invoked in a separate thread of control.
		This method will raise a RuntimeError if called more than once on the
		same thread object.
		"""
		if self._started.is_set():
			raise RuntimeError("threads can only be started once")

		with _active_limbo_lock:
			_limbo[self] = self
		try:
			start_new_thread(self._bootstrap, ())
		except Exception:
			with _active_limbo_lock:
				del _limbo[self]
			raise
		self._started.wait()

	def run(self):
		"""Method representing the thread's activity.
		You may override this method in a subclass. The standard run() method
		invokes the callable object passed to the object's constructor as the
		target argument, if any, with sequential and keyword arguments taken
		from the args and kwargs arguments, respectively.
		"""
		try:
			if self._target is not None:
				self._target(*self._args, **self._kwargs)
		finally:
			# Avoid a refcycle if the thread is running a function with
			# an argument that has a member that points to the thread.
			del self._target, self._args, self._kwargs

	def _bootstrap(self):
		# Wrapper around the real bootstrap code that ignores
		# exceptions during interpreter cleanup.  Those typically
		# happen when a daemon thread wakes up at an unfortunate
		# moment, finds the world around it destroyed, and raises some
		# random exception *** while trying to report the exception in
		# _bootstrap_inner() below ***.  Those random exceptions
		# don't help anybody, and they confuse users, so we suppress
		# them.  We suppress them only when it appears that the world
		# indeed has already been destroyed, so that exceptions in
		# _bootstrap_inner() during normal business hours are properly
		# reported.  Also, we only suppress them for daemonic threads;
		# if a non-daemonic encounters this, something else is wrong.
		try:
			self._bootstrap_inner()
		except:
			if self._daemonic and sys is None:
				return
			raise

	def _set_ident(self):
		self._ident = get_ident()

	def _set_tstate_lock(self):
		"""
		Set a lock object which will be released by the interpreter when
		the underlying thread state (see pystate.h) gets deleted.
		"""
		self._tstate_lock = _set_sentinel()
		self._tstate_lock.acquire()

		if not self.daemon:
			with _shutdown_locks_lock:
				_maintain_shutdown_locks()
				_shutdown_locks.add(self._tstate_lock)

	def _bootstrap_inner(self):
		try:
			self._set_ident()
			self._set_tstate_lock()
			self._started.set()
			with _active_limbo_lock:
				_active[self._ident] = self
				del _limbo[self]

			try:
				self.run()
			except:
				self._invoke_excepthook(self)
		finally:
			self._delete()

	def _stop(self):
		# After calling ._stop(), .is_alive() returns False and .join() returns
		# immediately.  ._tstate_lock must be released before calling ._stop().
		#
		# Normal case:  C code at the end of the thread's life
		# (release_sentinel in _threadmodule.c) releases ._tstate_lock, and
		# that's detected by our ._wait_for_tstate_lock(), called by .join()
		# and .is_alive().  Any number of threads _may_ call ._stop()
		# simultaneously (for example, if multiple threads are blocked in
		# .join() calls), and they're not serialized.  That's harmless -
		# they'll just make redundant rebindings of ._is_stopped and
		# ._tstate_lock.  Obscure:  we rebind ._tstate_lock last so that the
		# "assert self._is_stopped" in ._wait_for_tstate_lock() always works
		# (the assert is executed only if ._tstate_lock is None).
		#
		# Special case:  _main_thread releases ._tstate_lock via this
		# module's _shutdown() function.
		lock = self._tstate_lock
		if lock is not None:
			assert not lock.locked()
		self._is_stopped = True
		self._tstate_lock = None
		if not self.daemon:
			with _shutdown_locks_lock:
				# Remove our lock and other released locks from _shutdown_locks
				_maintain_shutdown_locks()

	def _delete(self):
		"Remove current thread from the dict of currently running threads."
		with _active_limbo_lock:
			del _active[get_ident()]
			# There must not be any python code between the previous line
			# and after the lock is released.  Otherwise a tracing function
			# could try to acquire the lock again in the same thread, (in
			# current_thread()), and would block.

	def join(self, timeout=None):
		"""Wait until the thread terminates.
		This blocks the calling thread until the thread whose join() method is
		called terminates -- either normally or through an unhandled exception
		or until the optional timeout occurs.
		When the timeout argument is present and not None, it should be a
		floating point number specifying a timeout for the operation in seconds
		(or fractions thereof). As join() always returns None, you must call
		is_alive() after join() to decide whether a timeout happened -- if the
		thread is still alive, the join() call timed out.
		When the timeout argument is not present or None, the operation will
		block until the thread terminates.
		A thread can be join()ed many times.
		join() raises a RuntimeError if an attempt is made to join the current
		thread as that would cause a deadlock. It is also an error to join() a
		thread before it has been started and attempts to do so raises the same
		exception.
		"""
		if not self._started.is_set():
			raise RuntimeError("cannot join thread before it is started")
		if self is current_thread():
			raise RuntimeError("cannot join current thread")

		if timeout is None:
			self._wait_for_tstate_lock()
		else:
			# the behavior of a negative timeout isn't documented, but
			# historically .join(timeout=x) for x<0 has acted as if timeout=0
			self._wait_for_tstate_lock(timeout=max(timeout, 0))

	def _wait_for_tstate_lock(self, block=True, timeout=-1):
		# Issue #18808: wait for the thread state to be gone.
		# At the end of the thread's life, after all knowledge of the thread
		# is removed from C data structures, C code releases our _tstate_lock.
		# This method passes its arguments to _tstate_lock.acquire().
		# If the lock is acquired, the C code is done, and self._stop() is
		# called.  That sets ._is_stopped to True, and ._tstate_lock to None.
		lock = self._tstate_lock
		if lock is None:
			# already determined that the C code is done
			assert self._is_stopped
			return

		try:
			if lock.acquire(block, timeout):
				lock.release()
				self._stop()
		except:
			if lock.locked():
				# bpo-45274: lock.acquire() acquired the lock, but the function
				# was interrupted with an exception before reaching the
				# lock.release(). It can happen if a signal handler raises an
				# exception, like CTRL+C which raises KeyboardInterrupt.
				lock.release()
				self._stop()
			raise

	@property
	def name(self):
		"""A string used for identification purposes only.
		It has no semantics. Multiple threads may be given the same name. The
		initial name is set by the constructor.
		"""
		return self._name

	@name.setter
	def name(self, name):
		self._name = str(name)

	@property
	def ident(self):
		"""Thread identifier of this thread or None if it has not been started.
		This is a nonzero integer. See the get_ident() function. Thread
		identifiers may be recycled when a thread exits and another thread is
		created. The identifier is available even after the thread has exited.
		"""
		return self._ident

	def is_alive(self):
		"""Return whether the thread is alive.
		This method returns True just before the run() method starts until just
		after the run() method terminates. See also the module function
		enumerate().
		"""
		if self._is_stopped or not self._started.is_set():
			return False
		self._wait_for_tstate_lock(False)
		return not self._is_stopped

	@property
	def daemon(self):
		"""A boolean value indicating whether this thread is a daemon thread.
		This must be set before start() is called, otherwise RuntimeError is
		raised. Its initial value is inherited from the creating thread; the
		main thread is not a daemon thread and therefore all threads created in
		the main thread default to daemon = False.
		The entire Python program exits when only daemon threads are left.
		"""
		return self._daemonic

def current_thread():
	"""Return the current Thread object, corresponding to the caller's thread of control.
	If the caller's thread of control was not created through the threading
	module, a dummy thread object with limited functionality is returned.
	"""
	try:
		return _active[get_ident()]
	except KeyError:
		return _DummyThread()

class _DummyThread(Thread):
	def __init__(self):
		global threadCount
		Thread.__init__(self, name=f"Dummy-{threadCount}", daemon=True)
		threadCount += 1
		self._started.set()
		self._set_ident()
		with _active_limbo_lock:
			_active[self._ident] = self


def _make_invoke_excepthook():
	# Create a local namespace to ensure that variables remain alive
	# when _invoke_excepthook() is called, even if it is called late during
	# Python shutdown. It is mostly needed for daemon threads.

	old_excepthook = excepthook
	old_sys_excepthook = sys.excepthook
	if old_excepthook is None or old_sys_excepthook is None:
		raise RuntimeError("excepthook is None")

	sys_exc_info = sys.exc_info
	local_print = print
	local_sys = sys

	def invoke_excepthook(thread):
		global excepthook
		try:
			hook = excepthook
			if hook is None:
				hook = old_excepthook

			args = ExceptHookArgs([*sys_exc_info(), thread])

			hook(args)
		except Exception as exc:
			exc.__suppress_context__ = True
			del exc

			stderr = local_sys.stderr if local_sys is not None and local_sys.stderr is not None else thread._stderr

			local_print("Exception in threading.excepthook:", file=stderr, flush=True)

			sys_excepthook = local_sys.excepthook if local_sys is not None and local_sys.excepthook is not None else old_sys_excepthook

			sys_excepthook(*sys_exc_info())
		finally:
			# Break reference cycle (exception stored in a variable)
			args = None

	return invoke_excepthook

def _maintain_shutdown_locks():
	"""
	Drop any shutdown locks that don't correspond to running threads anymore.
	Calling this from time to time avoids an ever-growing _shutdown_locks
	"""
	_shutdown_locks.difference_update([lock for lock in _shutdown_locks if not lock.locked()])
