

if __name__ == '__main__':
    from app.adapters.api.bilibili_api import get_videos_zones

    new_videos = []

    # B站分区视频扫描
    bilibili_rids = []
    zones = get_videos_zones()
    bilibili_rids.extend(zones.keys())
    for zone in zones.values():
        bilibili_rids.extend(zone.values())
    bilibili_rids = bilibili_rids[2:]