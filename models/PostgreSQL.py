import asyncpg
from . import AbstractDataBase
from asyncio import get_event_loop


class PostgreSQL(AbstractDataBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loop = get_event_loop()
        loop.create_task(self.create_db_and_connect())

    async def create_db_and_connect(self):
        await self.connect()
        await self.__create_weverse_schema()
        await self.__create_weverse_table()

    async def connect(self):
        self.pool: asyncpg.pool.Pool = await asyncpg.create_pool(**self._connect_kwargs, command_timeout=60)
        print("Successful Connection to DataBase.")
        return self.pool

    async def __create_weverse_schema(self):
        async with self.pool.acquire() as conn:
            await conn.execute(self._create_schema_sql)

    async def __create_weverse_table(self):
        async with self.pool.acquire() as conn:
            await conn.execute(self._create_table_sql)

    async def insert_weverse_channel(self, channel_id, community_name, media_enabled=True, comments_enabled=True):
        async with self.pool.acquire() as conn:
            await conn.execute(self._insert_channel_sql, channel_id, community_name.lower(), media_enabled,
                               comments_enabled, None)

    async def delete_weverse_channel(self, channel_id, community_name):
        async with self.pool.acquire() as conn:
            await conn.execute(self._delete_channel_sql, channel_id, community_name.lower())

    async def toggle_media(self, channel_id, community_name, current_status):
        async with self.pool.acquire() as conn:
            await conn.execute(self._toggle_media_sql, not current_status, channel_id, community_name.lower())

    async def toggle_comments(self, channel_id, community_name, current_status):
        async with self.pool.acquire() as conn:
            await conn.execute(self._toggle_comments_sql, not current_status, channel_id, community_name.lower())

    async def update_role(self, channel_id, community_name, role_id):
        async with self.pool.acquire() as conn:
            await conn.execute(self._update_role_sql, role_id, channel_id, community_name.lower())

    async def fetch_channels(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch(self._fetch_all_sql)
