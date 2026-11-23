# SPDX-License-Identifier: GPL-3.0-or-later
# Swiper jangan mencuri
#
#  Copyright (C) 2026  Asep5K
#
from yt_dlp.extractor.common import InfoExtractor
from typing import Any


class MiraiNimeIE(InfoExtractor):
    IE_NAME = 'mirainime'
    _VALID_URL = r'https://mirainime\.com/anime/(?P<slug>[^/]+)/episode/(?P<ep>\d+)$'
    # https://mirainime.com/anime/mononogatari-sub-indo/episode/3

    def _real_extract(self, url: str):
        slug, ep = self._match_valid_url(url).groups()
        video_id = f'{slug}-{ep}'
        webpage: str = self._download_webpage(url_or_request=url, video_id=video_id)

        player_opts: dict[str, str | Any] = self._search_json(
            r'window\.b2PlayerOptions\s*=', webpage, 'player options', video_id
        )

        exp: int = player_opts.get('streamTokens').get('exp')  # type:ignore

        sig: str = player_opts.get('streamTokens').get('sigs').get(ep)  # type:ignore

        data_streams: dict[str, str | Any] = self._download_json(
            f'https://mirainime.com/anime/{slug}/episode/{ep}/streams',
            video_id,
            headers={'Accept': 'application/json', 'X-Stream-Token': f'{exp}.{sig}', 'Referer': url},
        )
        formats: list[Any] = []
        for src in data_streams.get('gdriveSources') or []:
            if not (url := src.get('url')):  # type: ignore
                continue

            formats.append(
                {
                    'url': url,
                    'format_id': src.get('resolution').replace('p', '') + '-gdrive',  # type: ignore
                    'filesize': src.get('size', 0) or 0,  # type: ignore
                }
            )
        if (hls_url := data_streams.get('hlsUrl') or None):
            formats.extend(self._extract_m3u8_formats(m3u8_url=hls_url, video_id=slug, headers={
                'referer': 'https://mirainime.com/'
            },fatal=False))
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
    #var dynEpMax = 7;
    def _real_extract(self, url: str):
        slug = self._match_id(url)
        webpage = self._download_webpage(url, slug)
        count = self._search_regex(r'var\s+dynEpMax\s+=\s+(?P<max_ep>\d+);', webpage, 'max episode', group='max_ep')
        entries = []
        for i in range(1, int(count) +1):
            entries.append(self.url_result(
                url = f'https://mirainime.com/anime/{slug}/episode/{i}',
                video_title = slug,
                ie = 'MiraiNime',
                video_id = slug + '-' + str(i),
            ))
        return self.playlist_result(
            entries=entries,
            playlist_description=self._og_search_description(webpage)
        )

# vi: nowrap

