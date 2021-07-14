class TextChannel:
    def __init__(self, channel_id, role_id, media_enabled, comments_enabled):
        """
        Represents a discord Text Channel and the Weverse settings. Note that this is UNIQUE TO A WEVERSE COMMUNITY.
        It is not unique to it's text channel id.

        :param channel_id: Text Channel ID
        :param role_id: Role ID
        :param media_enabled: Whether media is enabled.
        :param comments_enabled: Whether comments are enabled.
        """
        self.id = channel_id
        self.role_id = role_id
        self.media_enabled = media_enabled
        self.comments_enabled = comments_enabled
        self.already_posted = []  # list of notification ids.
