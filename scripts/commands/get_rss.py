import datetime

from nio import MatrixRoom, Event

from nio import MatrixRoom, RoomMessage
from matrix_bot.client import MatrixClient
from matrix_bot.callbacks import properly_fail
from matrix_bot.eventparser import MessageEventParser, ignore_when_not_concerned

from scripts.command import Command
from typing_extensions import override

import feedparser 
import structlog

logger = structlog.getLogger(__name__)

class GetRssCommand(Command):
    KEYWORD = "get_rss"

    @staticmethod
    @override
    def needs_secure_validation() -> bool:
        return False
    
    def __init__(
        self, room: MatrixRoom, message: RoomMessage, matrix_client: MatrixClient
    ) -> None:
        super().__init__(room, message, matrix_client)

        event_parser = MessageEventParser(
            room=room, event=message, matrix_client=matrix_client
        )
        event_parser.do_not_accept_own_message()
        
        # il ne va répondre qu'au message "!get_rss"
        args = event_parser.command(self.KEYWORD).split()

        if len(args) > 0:
            self.rssUrl = args[0]
        else:
            self.rssUrl = None

    @override
    async def execute(self) -> bool:

        if self.rssUrl is None:
            rss_output = "You must provide a RSS source URL."
        else:
            rss_data = self.get_rss_content(self.rssUrl)

            rss_output = ""

            if rss_data: 
                for entry in rss_data['posts']:
                    rss_output += f"""• {entry['title']}: {entry['link']}\n"""
            else: 
                rss_output = "<no rss content>" 

        # il envoie l'information qu'il est en train d'écrire
        # await self.matrix_client.room_typing(self.room.room_id)
        # il envoie le message
        await self.matrix_client.send_text_message(self.room.room_id, rss_output)

        return True
    
    @override
    async def set_status_reaction(self, key: str | None) -> None:
        return
    
    def get_rss_content(self, rss=None): 
        # """ 
        # Take link of rss feed as argument 
        # """
        logger.info(f"""get_rss_content for {rss}""")

        if rss is not None: 
            # import the library only when url for feed is passed 
            
            # parsing blog feed 
            blog_feed = blog_feed = feedparser.parse(rss) 
            
            # getting lists of blog entries via .entries 
            posts = blog_feed.entries 
            
            # dictionary for holding posts details 
            posts_details = {"Blog title" : blog_feed.feed.title, 
                            "Blog link" : blog_feed.feed.link} 
            
            post_list = [] 
            
            # iterating over individual posts 
            for post in posts: 
                temp = dict() 
                
                # if any post doesn't have information then throw error. 
                try: 
                    temp["title"] = post.title 
                    temp["link"] = post.link 
                    temp["author"] = post.author 
                    temp["time_published"] = post.published 
                    temp["tags"] = [tag.term for tag in post.tags] 
                    temp["authors"] = [author.name for author in post.authors] 
                    temp["summary"] = post.summary 
                except: 
                    pass
                
                post_list.append(temp) 
            
            # storing lists of posts in the dictionary 
            posts_details["posts"] = post_list 
            
            return posts_details # returning the details which is dictionary 
        else: 
            return None