#
# query - uses splicer to simplify complex data manipulations
#

import splicer
from splicer.adapters.dict_adapter import DictAdapter

from . import commits
from . import docker

COMMIT_SCHEMA=[
  dict(name="branch", type="STRING"),
  dict(name="commit", type="STRING"),
  dict(name="rel_commit", type="INTEGER")
]

IMAGE_SCHEMA=[
  dict(name="image", type="STRING"),
  dict(name="tag", type="STRING")
]


def images(docker_client, containers):
  all_tags = docker.tags_from_containers(docker_client, containers)
  return [
    dict(image=container.name, tag=tag)
    for container, tags in zip(containers, all_tags)
    for tag in tags
  ]


def branches(source_control):
  return [
    dict(branch=branch.name, commit=commits.hexsha(commit), rel_commit=rel)
    for branch in source_control.branches
    for rel, commit in enumerate(commits.commits(source_control, branch))
  ]


def dataset(source_control, docker_client, containers):

  dataset = splicer.DataSet()

  # data collected at the start of the program
  static_data = DictAdapter(
    branch = dict(
      schema = dict(fields=COMMIT_SCHEMA),
      rows = branches(source_control)
    ),
    image = dict(
      schema = dict(fields=IMAGE_SCHEMA),
      rows = images(docker_client, containers)
    )
  )
  
  dataset.add_adapter(static_data)

  dataset.create_view(
    'latest_commit',
    'select branch.branch, branch.commit, max(branch.rel_commit) as rel_commit '
    'from image join branch on image.tag = branch.commit group by branch '
    'union all '
    # splicer doesn't have select distinct yet.. this is the equiv 
    'select branch, branch as commit, -1 from branch '
    'group by branch'
  )
  return dataset
