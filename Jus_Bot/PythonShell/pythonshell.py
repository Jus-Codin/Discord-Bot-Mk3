import sys
import subprocess
import asyncio
import signal

OUTPUT_MAX = 1000000
READ_CHUNK_SIZE = 10000
TIMEOUT = 10

async def python3(code: str):

  backend = '''
import sys
sys.modules['os'] = None
del sys
'''

  code = backend + code

  args = (
    sys.executable,
    '-E',
    '-I',
    '-c',
    code
  )

  python = await asyncio.create_subprocess_exec(
    *args,
    stdout = subprocess.PIPE,
    stderr = subprocess.STDOUT
  )

  output_size = 0
  output = []

  while python.returncode is None:
    try:
      chars = await asyncio.wait_for(python.stdout.read(READ_CHUNK_SIZE), TIMEOUT)
    except asyncio.TimeoutError:
      python.terminate()
      break

    output_size += sys.getsizeof(chars)
    output.append(chars)

    if output_size > OUTPUT_MAX:
      python.terminate()
      break
    
  output = ''.join([chunk.decode() for chunk in output])

  returncode = python.returncode if python.returncode is not None else signal.SIGTERM

  return subprocess.CompletedProcess(args, returncode, output, None)