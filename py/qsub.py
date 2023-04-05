#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
This file is part of tumorcode project.
(http://www.uni-saarland.de/fak7/rieger/homepage/research/tumor/tumor.html)

Copyright (C) 2016  Michael Welter and Thierry Fredrich

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import os,sys
import io
import base64
import pickle
import subprocess
import math
import time
import re

def printClientInfo():
  import socket
  print(('run this on client: %s' % socket.gethostname()))
  print(('invoked by: %s' % sys._getframe(1).f_code.co_name))
  print(('cwd: %s' % os.getcwd()))

__all__ = [ 'parse_args', 'submit', 'exe', 'func', 'is_client']

''' globals '''
#defaultMemory = '1MB'
#defaultDays = 42
#defaultNumThreads = 4
global goodArgumentsQueue
goodArgumentsQueue = {} #empty namespace
installed_queue_system = 'foo'
is_client = False


def parse_args(argv):
  import argparse
  parserQueue = argparse.ArgumentParser(prog='qsub',description='Queueing system parser.')
  memory_option = parserQueue.add_argument('-m', '--memory', help= 'Memory assigned by the queueing system', type=str, default = None)
  days_option = parserQueue.add_argument('-d', '--days', help= 'runtime for job in days', type=float, default = None)
  hours_option = parserQueue.add_argument('--hours', help= 'runtime for job in hours', type=float, default = None)
  threads_option = parserQueue.add_argument('-n', '--numThreads', help= 'num of threads for job', type=int, default = None)
  exclude_option = parserQueue.add_argument('--exclude', help= 'nodes to exclude', type=str, default = None)
  debub_option = parserQueue.add_argument('-D', '--Debug', help= 'if true, we submit do debug queue', default=False, action='store_true')
  cineca_knl_deb_option = parserQueue.add_argument('--knlDeb', help= 'if true, we submit to knl_usr_dbg queue', default=False, action='store_true')
  cineca_knl_option = parserQueue.add_argument('--knl', help= 'if true, we submit to knl_usr_prod queue', default=False, action='store_true')
#  global defaultMemory
#  defaultMemory = memory_option.default
#  global defaultDays
#  defaultDays = days_option.default
#  global defaultNumThreads
#  defaultNumThreads = threads_option.default
  parserQueue.add_argument('--q-local', help= ' Do not submit to queue, even if queuing system is pressent', default=False, action='store_true')
  parserQueue.add_argument('--q-dry', help= 'Do not run but print configuration to be submitted', default=False, action='store_true')
  parserQueue.add_argument('--q-verbose', help= 'more output', default=False, action='store_true')
  parserQueue.add_argument('--mpi', help='submits to mpi partition and allocates requested number of nodes', default=None, type=int)  
  localgoodArgumentsQueue, otherArgumentsQueue = parserQueue.parse_known_args()  
  global goodArgumentsQueue
  goodArgumentsQueue = localgoodArgumentsQueue



def identify_installed_submission_program_():
  qsys = os.environ.get('QUEUE_SUBMISSION_PROGRAM', None)
  if qsys:
    if qsys in ('qsub','sbatch'):
      return qsys
    else:
      print(('qsub.py WARNING: env. var. QUEUE_SUBMISSION_PROGRAM is set to unsupported "%s"' % qsys))
  # check if qsub is there
  try:
    subprocess.Popen(['qsub', '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
  except OSError as e:
    if goodArgumentsQueue.q_verbose:
      print ('qsub.py: we are not using qsub.')
  else:
    return 'qsub'
  #check if slurm works
  try:
    subprocess.Popen(['srun','--version'],stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
  except OSError as e:
    if goodArgumentsQueue.q_verbose:
      print('qsub.py: we are not using slurm')
  else:
    return 'sbatch'
  if goodArgumentsQueue.q_verbose: #opts_['run_verbose']:
    print('qsub.py: no supported queue system found.')
  return None

  
def determine_submission_program_():
  returnstring = 'return'
  if goodArgumentsQueue.q_local:
    returnstring = 'run_locally'
  else:
    returnstring = identify_installed_submission_program_()
    if returnstring is None:
      print('Warning: no supported queueing system found -> run locally')
      returnstring = 'run_locally'
  return returnstring



def fmtDate_(days, hours):
    '''turn any number of days and hours into hours h which are
       0 <= d < 24. Also handle fractional days and hours. Fractional
       hours are simply rounded up to full hours.'''
    if days is None:
        days = 0
    if hours is None:
        hours = 0
        
    int_hours = math.floor(hours)
    broken_hours = hours-int_hours
    minutes = broken_hours*60
    print(('days: %i, hours: %i, minutes: %i' %(days,hours,minutes)))
    return int(days), int(int_hours), int(minutes)
    

def write_directives_qsub_(f,name=None, mem=None, num_cpus=None, days=None, hours=None, outdir=None, export_env=False, jobfiledir=None, change_cwd=False, dependsOnJob = None):
#  mem =goodArgumentsQueue.memory
#  num_cpus = goodArgumentsQueue.numThreads
#  days = goodArgumentsQueue.days
  print('#PBS -j oe', file=f)
  if jobfiledir and not outdir: #DEPRECATED
    outdir = jobfiledir
  if outdir is not None:
    print('#PBS -o %s' % (outdir), file=f)
  if name:
    print('#PBS -N %s' % name, file=f)
  if num_cpus > 1:
    print('#PBS -l nodes=1:ppn=%i' % num_cpus, file=f)
  if days or hours:
    days, hours = fmtDate_(days, hours)
    print('#PBS -l walltime=%i:00:00' % max(1, hours + days*24), file=f)
#  mem =goodArgumentsQueue.memory
  if mem:
    if re.match(r'^\d+(kB|MB|GB)$', mem) is None:
      raise RuntimeError('mem argument needs integer number plus one of kB, MB, GB')
    print('#PBS -l mem=%s' % mem, file=f)
  if export_env:
    print('#PBS -V', file=f)
  if dependsOnJob:
    print('#PBS -W depend=afterok:%s' % dependsOnJob, file=f)
    
    
def write_directives_slurm_(f, num_cpus=None, mem=None, name=None, days=None, hours=None, outdir=None, export_env=False, jobfiledir=None, change_cwd=False, dependOn=None):
  hpc_system = os.environ.get('HPC_SYSTEM', None)
  if goodArgumentsQueue.exclude:
    print('#SBATCH --exclude=%s' % goodArgumentsQueue.exclude, file=f)
    
  if dependOn is not None:
    print('#SBATCH --dependency=afterok:%i' % dependOn, file=f)
    
  if hpc_system == 'marconi':
    print('#SBATCH --account=uTS18_Milotti', file=f)
    if name:
      print('#SBATCH --job-name=%s' % name, file=f)
      
    if num_cpus == 1:
      print('#SBATCH --cpus-per-task=1', file=f)
      print('#SBATCH --ntasks=1', file=f)
      
    if num_cpus > 1 and not goodArgumentsQueue.mpi:
      print('#SBATCH --cpus-per-task=%i' % num_cpus, file=f)
      print('#SBATCH --ntasks=1', file=f)
      print('#SBATCH --nodes=1', file=f)
      print('#SBATCH --ntasks-per-node=1', file=f)
      
    if goodArgumentsQueue.knl:
      print('knl_usr_prod chosen')
      print('#SBATCH --partition=knl_usr_prod', file=f)
    if goodArgumentsQueue.knlDeb:
      print('knl_usr_dbg chosen')
      print('#SBATCH --partition=knl_usr_dbg', file=f)
      #print >>f, '#SBATCH --time=0-00:10:00'
    #else:
      #print >>f, '#SBATCH --partition=bdw_usr_prod'
      #if goodArgumentsQueue.cinecaSpecial:
      #  print >>f, '#SBATCH --qos=bdw_qos_special'
    if days or hours:
      days, hours, minutes = fmtDate_(days, hours)#not used on cinceca
      days=0 #needs to be guaranteed in cineca
      print('#SBATCH --time=%i-%i:%i:00' % (days, hours,minutes), file=f)
      
    if mem:
      print('cineca chosen mem below 110 GB')
      if re.match(r'^\d+(kB|MB|GB)$', mem) is None:
        raise RuntimeError('mem argument needs integer number plus one of kB, MB, GB')
      print('#SBATCH --mem=%s' % mem, file=f)
#    print >>f, 'export OMP_NUM_THREADS=%i' % num_cpus
      
    
  if not hpc_system:#### SNOWDEN
    if name:
      print('#SBATCH --job-name=%s' % name, file=f)
    if num_cpus == 1:
      print('#SBATCH --cpus-per-task=1', file=f)
      print('#SBATCH --ntasks=1', file=f)
      print('#SBATCH --partition=onenode', file=f)
    if not goodArgumentsQueue.Debug:
      if num_cpus > 1 and not goodArgumentsQueue.mpi:
        print('#SBATCH --cpus-per-task=%i' % num_cpus, file=f)
        print('#SBATCH --ntasks=1', file=f)
        print('#SBATCH --nodes=1', file=f)
        print('#SBATCH --partition=onenode', file=f)
        print('#SBATCH --ntasks-per-node=1', file=f)
        # this is for sparing the nodes with lots of cores
        #print >>f, '#SBATCH --exclude=leak[57-64]'
        #print >>f, '#SBATCH --nodelist=leak62'
        #print >>f, '#SBATCH --resv-ports'
      #MPI
      if num_cpus > 1 and goodArgumentsQueue.mpi:
        print('#SBATCH --cpus-per-task=%i' % num_cpus, file=f)
    #    print >>f, '#SBATCH --ntasks=50'
        print('#SBATCH --ntasks-per-node=1', file=f)
        print('#SBATCH --nodes=%i' % goodArgumentsQueue.mpi, file=f)
        print('#SBATCH --partition=mpi', file=f)
    #    print >>f, '#SBATCH --resv-ports'
    #    print >>f, '#SBATCH --ntasks-per-node=8'
    else:#DEBUG
      print('#SBATCH --cpus-per-task=%i' % num_cpus, file=f)
      print('#SBATCH --ntasks=1', file=f)
      print('#SBATCH --nodes=1', file=f)
      print('#SBATCH --partition=debug', file=f)
      print('#SBATCH --ntasks-per-node=1', file=f)
    
    if days or hours:
      days, hours, minutes = fmtDate_(days, hours)
      print('#SBATCH --time=%i-%i:%i:00' % (days, hours, minutes), file=f)
    if mem:
      if re.match(r'^\d+(kB|MB|GB)$', mem) is None:
        raise RuntimeError('mem argument needs integer number plus one of kB, MB, GB')
      print('#SBATCH --mem=%s' % mem, file=f)
      if num_cpus > 1:
        mem_per_cpu='8500MB'
        print('#SBATCH --mem-per-cpu=%s' % mem_per_cpu, file=f)
    #if export_env:
    #  print >>f, '#PBS -V'


def submit_(interpreter, submission_program, script):
  #global opts_
  # determine how to run
  print(("interpreter: %s, submission_program: %s" %(interpreter, submission_program)))
  if submission_program == 'run_locally':
    submission_program = interpreter
  # verbose output
  if goodArgumentsQueue.q_verbose or goodArgumentsQueue.q_dry:
    print((' submission to %s ' % submission_program).center(30,'-'))
    print(script)
    print(''.center(30,'-'))
  # run stuff
  # incase there is no queue e.g. local runs
  jobID = 0
  if not goodArgumentsQueue.q_dry:
    time.sleep(0.2)
    if submission_program == 'python' or submission_program == 'python_debug': # running python script with python locally?!! We can do it like so
      print("calling python:")
      exec(script, dict(), dict())
    else: # all the other cases go like so!
      print("calling subprocess:")
      #return_from_queuing_system = subprocess.call("%s <<EOFQSUB\n%s\nEOFQSUB" % (submission_program, script), shell=True)
      p1 = subprocess.Popen("%s <<EOFQSUB\n%s\nEOFQSUB" % (submission_program, script), stdout=subprocess.PIPE,shell=True)
      return_from_queuing_system = p1.communicate()[0]
      prog = determine_submission_program_()
      jobID = 0
      if prog == 'sbatch':
        ''' expect return of form "Submitted batch job 3522973'''
        jobID= int(return_from_queuing_system.split()[-1])
        #print(return_from_queuing_system.split()[-1])
      else:
              print("Error, no queuing system identified")
      #print(return_from_queuing_system)
      #subprocess.check_output("%s <<EOFQSUB\n%s\nEOFQSUB" % (submission_program, script), shell=True)
  return jobID

pyfuncscript_ = """\
import imp as imp__
import pickle as cPickle__
import base64 as base64__
import sys
sys.path.append('%s')
qsub = __import__('qsub', globals(), locals())
setattr(qsub, 'is_client', True)
%s
from your_module__ import *
args__, kwargs__ = cPickle__.loads(base64__.urlsafe_b64decode(%s))
%s(*args__, **kwargs__)
"""
pychangecwd_ = """\
import os as os__
try: os__.chdir('%s')
except KeyError: pass
"""


class Func(object):
  '''
    A Wrapper around a function call. This allows you to submit python function calls to qsub.

    It does this by submitting a small 'outer' script which imports the module in which the
    function resides and calls the function by its name with the supplied parameters.
    Therefore your script must be file on the filesystem. It does not work in interactive mode.

    WARNING: Your script is NOT COPIED! It is loaded as is at the time of execution on the
    cluster node. This is inconsistent with the normal behavior of qsub!

    You give an object of this kind to the submit function in order to run it.
  '''
  if sys.flags.debug:
    interpreter = 'python_debug'
  else:
    interpreter = 'python'
  def __init__(self, func, *args, **kwargs):
    self.func = func
    self.args = (args, kwargs)
    self.name_hint = func.__name__

  def generate_script(self, qsubopts):
    func, (args, kwargs) = self.func, self.args
    # generate the python script
    a = base64.urlsafe_b64encode(pickle.dumps((args,kwargs)))
    # doesn't work so well because if the module is not the main module,
    # the __module__ variable can point to something else than the file 
    # where func is defined. Example: /py/krebsjobs/__init__.pyc instead
    # of /krebsjobs/submitDetailedO2.py!
    #   m = __import__(func.__module__)
    #   filename = os.path.abspath(m.__file__)
    # next try:
    filename = func.__globals__['__file__']  # seems simple enough?! '__globals__' just contains the global variables that the function sees.
    filename = os.path.abspath(filename) # don't want to get in trouble because of changing work dir
    functionname = func.__name__
    if filename.endswith('.pyc'):
      load_string = "your_module__ = imp__.load_compiled('your_module__', '%s')" % filename
    else:
      load_string = "your_module__ = imp__.load_source('your_module__', '%s')" % filename
    s = pyfuncscript_ % (os.path.abspath(os.path.dirname(__file__)), load_string, a, functionname)
    if qsubopts.get('change_cwd', False):
      s = (pychangecwd_ % os.getcwd()) + s
    return s

func = Func




class Exe(object):
  '''
    A wrapper around a system call to execute a program.

    You give an object of this kind to the submit function in order to run it.

    cmd - string or sequence of objects which can be converted to strings
  '''
  interpreter = 'sh'
  def __init__(self, *cmds):
    for i, cmd in enumerate(cmds):
      if isinstance(cmd, str) or not hasattr(cmd, '__iter__'):
        cmds[i] = [cmd]
    self.cmds = cmds
    self.name_hint = None
  def generate_script(self, qsubopts):
    lines = [
      ' '.join(list(str(q) for q in cmd)) for cmd in self.cmds
      ]
    '''add OpenMP setting from slurm '''
    lines = ['export OMP_NUM_THREADS=%i'% os.environ.get('SLURM_JOB_CPUS_PER_NODE',0)] + lines
    if qsubopts.get('change_cwd', False):
      lines = [ 'cd %s' % os.getcwd() ] + lines
    return '\n'.join(lines)

exe = Exe
#
#class SrunExe(object):
#  '''
#    A wrapper around a system call to execute a program.
#
#    You give an object of this kind to the submit function in order to run it.
#
#    cmd - string or sequence of objects which can be converted to strings
#  '''
#  interpreter = 'sh'
#  def __init__(self, *cmds):
#    for i, cmd in enumerate(cmds):
#      if isinstance(cmd, str) or not hasattr(cmd, '__iter__'):
#        cmds[i] = [cmd]
#    self.cmds = cmds
#    self.name_hint = None
#  def generate_script(self, qsubopts):
#    lines = [
#      ' '.join(list(str(q) for q in cmd)) for cmd in self.cmds
#      ]
#    if qsubopts.get('change_cwd', False):
#      lines = [ 'cd %s' % os.getcwd() ] + lines
#    return '\n'.join(lines)
#
#sexe = SrunExe    


def submit_qsub(obj, submission_program, **qsubopts):
  '''
    Run stuff with qsub. See Exe and Func.
    Qsub parameters are special. WARNING: parameters might change!

    qsubopts can contain:
      name -> job name (string)
      days -> runtime in days (any number)
      num_cpus -> processors per job (int)
      mem -> memory usage (string)
      outdir -> directory where stdout/err are written to (string)
      export_env -> export current environment to launched script (bool)
  '''
  # default name
  if not 'name' in qsubopts:
    if obj.name_hint:
      qsubopts['name'] = obj.name_hint
    else:
      qsubopts['name'] = 'unnamed'
  # interpreter string
  cases = {
    'sh' : '#!/bin/sh',
    'python' : ('#!/usr/bin/env python%i'  % sys.version_info.major),
    'python_debug' : ('#!/usr/bin/python%i -d'  % sys.version_info.major)
  }
  first_line = cases[obj.interpreter]
  # add qsub stuff + python script
  f = io.StringIO()
  print(first_line, file=f)
  if not submission_program == 'run_locally':
    write_directives_qsub_(f, **qsubopts)
  print(obj.generate_script(qsubopts), file=f)
  return submit_(obj.interpreter, submission_program, f.getvalue())
  

def submit_slurm(obj, submission_program, **slurmopts):
  '''
    Run stuff with slurm. See Exe and Func.
    Slurm parameters are special. WARNING: parameters might change!
  '''
  # default name
  if not 'name' in slurmopts:
    if obj.name_hint:
      slurmopts['name'] = obj.name_hint
    else:
      slurmopts['name'] = 'unnamed'
  # interpreter string
  cases = {
    'sh' : '#!/bin/sh',
    'python' : ('#!/usr/bin/env python%i'  % sys.version_info.major),
    'python_debug' : ('#!/usr/bin/python%i -d'  % sys.version_info.major),
    'debug_hardcore' : '#!/bin/sh',                  
    #'python' : '#!/bin/sh'
  }
  first_line = cases[obj.interpreter]
  #print first_line
  # add qsub stuff + python script
  f = io.StringIO()
  print(first_line, file=f)
  write_directives_slurm_(f, **slurmopts)
  #print >>f, 'import os'
  #print >>f, 'os.environ[''OMP_NUM_THREADS'']=os.environ[''SLURM_JOB_CPUS_PER_NODE'']'
  #print >>f, 'print(os.environ[''OMP_NUM_THREADS''])'
  old=True
  if old:
    print(obj.generate_script(slurmopts), file=f)
    return submit_(obj.interpreter,submission_program, f.getvalue())
  else:
    print('echo "Maybe a stupid idea, but I will create a .py file now"', file=f)
    string_abuffer_name = 'buffer_%s.py' % time.time()
    if 'thierry_slurm_buffer' not in os.listdir('/localdisk/tmp'):
      os.mkdir('/localdisk/tmp/thierry_slurm_buffer')
      mypyscriptfile = open('/localdisk/tmp/thierry_slurm_buffer/%s' % string_abuffer_name,"w+")
      mypyscriptfile.write(obj.generate_script(slurmopts))
      mypyscriptfile.close()
      if obj.interpreter == 'python':
        #print >>f, ('srun --resv-port mpirun /usr/bin/python3 %s' % mypyscriptfile.name)
        print(('/usr/bin/python3 %s' % mypyscriptfile.name), file=f)
      if obj.interpreter == 'sh':
        #print >>f, ('srun --resv-port mpirun /bin/sh %s' % mypyscriptfile.name)
        print(('/bin/sh %s' % mypyscriptfile.name), file=f)
        print((f.getvalue()))
        #print(f.getvalue())
        #print >>f, obj.generate_script(slurmopts)
        #print(f.getvalue())
        submit_('sh', submission_program, f.getvalue())


def submit(obj, **qsubopts):
#    if 'mem' in qsubopts and goodArgumentsQueue.memory == defaultMemory:
#      print('Memory setting provided by program')
#      global goodArgumentsQueue
#      goodArgumentsQueue.memory = qsubopts.pop('mem')
#    if not goodArgumentsQueue.memory == defaultMemory:
#      if 'mem' in qsubopts:
#        print('OVERRIDE Memory setting provided by program')
#        print('was: %s, will be: %s '%(qsubopts['mem'], goodArgumentsQueue.memory))
#        qsubopts.pop('mem') #pop and not storing!!!
#    if 'days' in qsubopts and goodArgumentsQueue.days == defaultDays:
#      print('Days setting provided by program')
#      global goodArgumentsQueue
#      goodArgumentsQueue.days = qsubopts.pop('days')
#    if not goodArgumentsQueue.days == defaultDays:
#      if 'days' in qsubopts:
#        print('OVERRIDE days setting provided by program')
#        print('was: %s, will be: %s '%(qsubopts['days'], goodArgumentsQueue.days))
#        qsubopts.pop('days') #pop and not storing!!!
#    if 'num_cpus' in qsubopts and goodArgumentsQueue.numThreads == defaultNumThreads:
#      print('threads setting provided by program')
#      global goodArgumentsQueue
#      goodArgumentsQueue.numThreads = qsubopts.pop('num_cpus')
#    if not goodArgumentsQueue.numThreads == defaultNumThreads:
#      if 'num_cpus' in qsubopts:
#        print('OVERRIDE thread setting provided by program')
#        print('was: %s, will be: %s '%(qsubopts['num_cpus'], goodArgumentsQueue.numThreads))
#        qsubopts.pop('num_cpus')
        
    #print(goodArgumentsQueue.memory)
    #print(defaultMemory)
    '''
    override parameters set by read in from files
    by command line arguments
    '''
    #  mem = goodArgumentsQueue.memory
#  num_cpus = goodArgumentsQueue.numThreads
#  days = goodArgumentsQueue.days
    if goodArgumentsQueue.numThreads:
      qsubopts['num_cpus'] = goodArgumentsQueue.numThreads
      print(('override thread with from %i to %i' % (qsubopts['num_cpus'],goodArgumentsQueue.numThreads)))
      
    if goodArgumentsQueue.memory:
      qsubopts['mem'] = goodArgumentsQueue.memory
      print(('override memory with from %s to %s' % (qsubopts['mem'],goodArgumentsQueue.memory)))
      
    if goodArgumentsQueue.days:
      qsubopts['days'] = goodArgumentsQueue.days
      print(('override time from %f to %f' % (qsubopts['days'],goodArgumentsQueue.days)))
      
    if goodArgumentsQueue.hours:
      qsubopts['hours'] = goodArgumentsQueue.hours
      print(('override time hours from %f to %f' % (qsubopts['hours'],goodArgumentsQueue.hours)))
      
    
    if sys.flags.debug:
      print(qsubopts)
    
    print("goodArgumentsQueue")
    print(goodArgumentsQueue)
    prog = determine_submission_program_()
    print(("determined program: %s" %prog))
    
    jobID = 0
    if prog == 'sbatch':
      jobID = submit_slurm(obj, prog, **qsubopts)
    elif prog == 'qsub':
      submit_qsub(obj, prog, **qsubopts)
    elif prog == 'run_locally':
      submit_qsub(obj, prog, **qsubopts)
    else:
      print("unknow submission sytem")
    print(("submitting with jobID: %i" % jobID))
    return jobID
      
if __name__ == '__main__':
  print((fmtDate_(0, 3.5)))
  
