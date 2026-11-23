# SPDX-License-Identifier: GPL-3.0-or-later
# Swiper jangan mencuri
#
#  Copyright (C) 2026  Asep5K
#
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import parse_resolution
from typing import Any
import re

class MiraiNimeIE(InfoExtractor):
    IE_NAME = 'mirainime'
    _VALID_URL = r'https://mirainime\.com/anime/(?P<slug>[^/]+)/episode/(?P<ep>\d+)$'
    # https://mirainime.com/anime/mononogatari-sub-indo/episode/3
    _data_stream_cache = {}

    def _real_extract(self, url: str):
        slug ,ep= self._match_valid_url(url).groups()
        video_id = f'{slug}-{ep}'
        webpage: str = self._download_webpage(url_or_request=url, video_id=video_id)

        player_opts: dict[str, str | Any] = self._search_json(
            start_pattern= r'window\.b2PlayerOptions\s*=', string=webpage, name='player options',video_id=video_id
        )

        exp: int = player_opts.get('streamTokens').get('exp')  # type:ignore
        sig: str = player_opts.get('streamTokens').get('sigs').get(ep)  # type:ignore

        if not self._data_stream_cache.get(slug):
            self._data_stream_cache[slug]: dict[str, str | Any] = self._download_json(
                f'https://mirainime.com/anime/{slug}/episode/{ep}/streams',
                video_id,
                headers={'Accept': 'application/json', 'X-Stream-Token': f'{exp}.{sig}', 'Referer': url},
            )

        data_streams = self._data_stream_cache[slug]
        if (hls_url := data_streams.get('hlsUrl') or '') != '':
            formats:list[dict[str,str|int]] = self._extract_m3u8_formats(m3u8_url=hls_url, video_id=slug, headers={
                'referer': 'https://mirainime.com/'
            },fatal=False) or []
        else:
            formats:list[dict[str,str|int]]= []

        for src in data_streams.get('gdriveSources') or []:
            if not (url := src.get('url')):
                continue
            res: str = src.get("resolution") or '0'
            formats.append(
                {
                    'url': url,
                    'format_id': f'{res.replace("p", "")}',
                    'filesize': src.get('size', 0) or 0,
                    'format_note': 'gdrive',
                    **parse_resolution(res),
                }
            )
        return {
            'id': str(object=player_opts.get('episodeId', video_id)),
            'title': self._og_search_title(html=webpage),
            'episode_number': int(ep),
            'formats': formats,
            'http_headers': {
                'Referer': 'https://mirainime.com/',
            },
        }


class MiraiNimePlaylistIE(MiraiNimeIE):
    IE_NAME = MiraiNimeIE.IE_NAME + ':playlist'
    _VALID_URL = r'https?://mirainime\.com/anime/(?P<id>[\w-]+)'
    # https://mirainime.com/anime/yozakura-san-chi-no-daisakusen-season-2-part-2
    # https://mirainime.com/anime/ushiro-no-shoumen-sub-indo
    #var dynEpMax = 7;
    def _real_extract(self, url: str):
        slug: str = self._match_id(url)
        webpage:str = self._download_webpage(url, slug)
        regex = rf'''(?sx)
        <a\s*href="(?P<url>https://mirainime\.com/anime/{slug}/episode/\d+)".*?
        (?:(?!</a>).)*?
        <img\s*src="(?P<thumb>[^"]+)"'''

        entries:list[dict[str, str|int]] = []
        for match_url in re.finditer(pattern=regex,string=webpage):
            if match_url:
                entries.append(self.url_result(
                    url_transparent=True,
                    url= (url := match_url.group('url')),
                    ie='MiraiNime', 
                    video_id=f'{slug}-{(ep :=url[-1])}',
                    thumbnail=match_url.group('thumb'),
                    video_title=f'{slug} Episode {ep}',
                    episode_number=int(ep),
                ))

        return self.playlist_result(
            entries=entries,
            playlist_id=slug,
            playlist_title=self._og_search_title(html=webpage)or slug,
        )
# vi: nowrap

