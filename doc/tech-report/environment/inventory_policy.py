"""Separate GPU-only experiments from CPU and static inspection commands."""

def gpu_only(command):
    for prefix in ('CUDA_VISIBLE_DEVICES="" ', "CUDA_VISIBLE_DEVICES='' ", 'CUDA_VISIBLE_DEVICES= '):
        command = command.removeprefix(prefix)
    if command.startswith(('grep ', 'git ')):
        return False
    return ('cuda' in command.lower() or 'cuobjdump' in command or '--compare' in command
            or 'check_ch12_' in command and 'conditioning' not in command
            or 'gpu_probe' in command or 'sparse_vs_dense' in command)
