import os
import re

import requests
from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class GithubFileDownloader:
    def download(self, api_url, target_folder_path, resource_name_regex):
        logger.info("Checking if the needed tools need to be downloaded...")

        if not os.path.exists(target_folder_path):
            logger.debug(f"Created {target_folder_path} folder")
            os.makedirs(target_folder_path)

        if not os.path.exists(os.path.join(target_folder_path, resource_name_regex)):
            response = requests.get(url=api_url).json()

            for asset in response["assets"]:
                url = asset["browser_download_url"]
                path, name = os.path.split(url)

                if not re.match(rf"{resource_name_regex}", name):
                    continue

                logger.info(f"Downloading [{colored(name, 'yellow')} from [{url}]")

                command = CommandGenerator() \
                    .wget() \
                    .parameters("--no-clobber", "-P", target_folder_path, url)

                CommandExecutor().execute(command)
                return name
