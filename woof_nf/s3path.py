import pathlib
import re


import boto3


from . import log


MESSAGE_LOGGED = False
S3_PATH_RE = re.compile(r'^s3://([^/]+)/?(.*?)$')


class VirtualPath():

    def __init__(self, paths, current_path='root'):
        self.paths = paths
        if current_path == 'root':
            assert len(paths[current_path]) == 1
            self.current_path = list(paths[current_path])[0]
        else:
            self.current_path = current_path

    def __str__(self):
        return self.current_path

    def is_dir(self):
        return self.current_path.endswith('/')

    def iterdir(self):
        for path in self.paths[self.current_path]:
            yield self.__class__(self.paths, path)

    @property
    def name(self):
        # Allows interop with pathlib.Path
        return pathlib.Path(self.current_path).name


def process_paths(s3_path_info, run):
    virtual_paths = list()
    for i, d in enumerate(s3_path_info, 1):
        log.render(f'  processing run {run}: path {i}/{len(s3_path_info)}...', end='\r', flush=True)
        # Get a list of all objects in bucket with given prefix
        s3_bucket = boto3.resource('s3').Bucket(d['bucket'])
        paths = [f'{d["bucket"]}/{r.key}' for r in s3_bucket.objects.filter(Prefix=d['key'])]
        # Create a virtual file path set
        vpath = create_virtual_paths(paths, d['bucket'], d['key'])
        virtual_paths.append(vpath)
    log.render(f'  processing run {run}: path {i}/{len(s3_path_info)}... done', flush=True)
    return virtual_paths


def create_virtual_paths(path_list, bucket, prefix):
    paths = dict()
    for fp in path_list:
        # Normalise path and then split into parts
        fp_normalised = fp.replace('//', '/')
        parts = fp_normalised.split('/')
        parts[0] = f's3://{parts[0]}'
        # Iterate and create a flat dict with parent dirs mapping to children:
        #   directory -> contents
        path_parent = 'root'
        path = str()
        for i, part in enumerate(parts, 1):
            if i == len(parts):
                path += part
            else:
                path += f'{part}/'
            if path_parent not in paths:
                paths[path_parent] = set()
            paths[path_parent].add(path)
            path_parent = path
    current_path = f's3://{bucket}/{prefix}'
    if not current_path.endswith('/'):
        current_path += '/'
    return VirtualPath(paths, current_path=current_path)
