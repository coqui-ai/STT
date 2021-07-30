from os import makedirs, path

from tqdm import tqdm
import progressbar
import requests

from .io import is_remote_path, open_remote, path_exists_remote

SIMPLE_BAR = [
    "Progress ",
    progressbar.Bar(),
    " ",
    progressbar.Percentage(),
    " completed",
]


def maybe_download(archive_name, target_dir, archive_url):
    # If archive file does not exist, download it...
    archive_path = path.join(target_dir, archive_name)

    if not is_remote_path(target_dir) and not path.exists(target_dir):
        print('No path "%s" - creating ...' % target_dir)
        makedirs(target_dir)

    if not path_exists_remote(archive_path):
        print('No archive "%s" - downloading...' % archive_path)
        req = requests.get(archive_url, stream=True)
        total_size = int(req.headers.get("content-length", 0))
        with open_remote(archive_path, "wb") as f:
            with tqdm(total=total_size) as bar:
                for data in req.iter_content(1024 * 1024):
                    f.write(data)
                    bar.update(len(data))
    else:
        print('Found archive "%s" - not downloading.' % archive_path)
    return archive_path
