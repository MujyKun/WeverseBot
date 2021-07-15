class AbstractDataBase:
    """
    Abstract Base for a DataBase.

    Inherit this class in a new model if you are using a different DB.
    """
    def __init__(self, host, database, user, password, port, schema_name="weversebot", table_name="channels"):
        self.pool = None

        self.host = host
        self._database = database
        self.user = user
        self.port = port
        self._password = password

        self._connect_kwargs = {
            "host": self.host,
            "database": self._database,
            "user": self.user,
            "password": self._password,
            "port": self.port
        }

        self._schema_name = schema_name
        self._table_name = table_name
        self._create_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {self._schema_name}"
        self._create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self._schema_name}.{self._table_name}
            (
                id serial,
                channelid bigint,
                communityname text,
                roleid bigint,
                comments boolean,
                media boolean,
                PRIMARY KEY (id)
            )
        """
        self._insert_channel_sql = f"INSERT INTO {self._schema_name}.{self._table_name}(channelid, communityname, " \
                                   f"media, comments, roleid) VALUES($1, $2, $3, $4, $5)"
        self._delete_channel_sql = f"DELETE FROM {self._schema_name}.{self._table_name} WHERE channelid = $1 AND " \
                                   f"communityname = $2"
        self._toggle_sql = f"UPDATE {self._schema_name}.{self._table_name} SET column_name=$1 WHERE channelid = " \
                           f"$2 AND communityname = $3"
        self._toggle_media_sql = self._toggle_sql.replace("column_name", "media")
        self._toggle_comments_sql = self._toggle_sql.replace("column_name", "comments")
        self._update_role_sql = self._toggle_sql.replace("column_name", "roleid")
        self._fetch_all_sql = f"SELECT channelid, communityname, roleid, media, comments FROM " \
                              f"{self._schema_name}.{self._table_name}"
        self._drop_schema_sql = f"DROP SCHEMA IF EXISTS {self._schema_name}"
        self._drop_table_sql = f"DROP TABLE IF EXISTS {self._schema_name}.{self._table_name}"

    async def connect(self):
        """Create the connection for the DataBase."""
        ...

    async def __create_weverse_schema(self):
        """Create the Weverse Schema."""
        ...

    async def __create_weverse_table(self):
        """Create the Weverse channels table."""
        ...

    async def insert_weverse_channel(self, channel_id, community_name, media_enabled=True, comments_enabled=True):
        """Insert a weverse channel.

        :param channel_id: (int) Text Channel ID.
        :param community_name: (str) The name of the community.
        :param media_enabled: (bool) Whether media should be enabled.
        :param comments_enabled: (bool) Whether commends should be enabled.
        """
        ...

    async def delete_weverse_channel(self, channel_id, community_name):
        """Unfollow a weverse community.

        :param channel_id: (int) Text Channel ID.
        :param community_name: (str) The name of the community.
        """
        ...

    async def toggle_media(self, channel_id, community_name, current_status: bool):
        """Toggle the media status of a channel.

        :param channel_id: (int) Text Channel ID.
        :param community_name: (str) The name of the community.
        :param current_status: (bool) The current comment status.
        """
        ...

    async def toggle_comments(self, channel_id, community_name, current_status: bool):
        """Toggle the comment status of a channel.

        :param channel_id: (int) Text Channel ID.
        :param community_name: (str) The name of the community.
        :param current_status: (bool) The current comment status.
        """
        ...

    async def update_role(self, channel_id, community_name, role_id):
        """Update the role for a channel.

        :param channel_id: (int) Text Channel ID.
        :param community_name: (str) The name of the community.
        :param role_id: (int) The Role ID.
        """
        ...

    async def fetch_channels(self):
        """Fetch channels, the channels they are following, and the media/comment status."""
        ...

    async def recreate_db(self):
        """Will update the database by dropping the table and recreating it with the new sql."""
        ...
