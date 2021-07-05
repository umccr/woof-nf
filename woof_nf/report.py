import pathlib
import subprocess
import sys
import textwrap


from . import log


def render(output_dir: pathlib.Path) -> None:
    log.task_msg_title('Rendering RMarkdown report')
    log.render_newline()
    output_fp = output_dir / 'report.html'
    lib_dir = pathlib.Path(__file__).parent / 'workflow/lib'
    rscript = textwrap.dedent(f'''
        library(rmarkdown)
        rmarkdown::render(
          '{lib_dir / "report.Rmd"}',
          output_file='{output_fp.absolute()}',
          params=list(
            results_directory='{output_dir.absolute()}'
          )
        )
    ''')
    p = subprocess.run(
        f'R --vanilla <<EOF\n{rscript}\nEOF',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        encoding='utf-8'
    )
    if p.returncode != 0:
        log.render(f'error:\n{p.stderr}')
        sys.exit(1)
