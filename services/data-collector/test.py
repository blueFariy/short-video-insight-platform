

if __name__ == '__main__':
    from app.adapters.api.bilibili_api import get_videos_zones,get_main_zones_by_category

    zones = get_videos_zones()
    bilibili_rids = []
    for zone in zones.values():
        bilibili_rids.extend(zone.values())
    bilibili_rids = bilibili_rids[:1]  # 去除主站与VLOG
    print(bilibili_rids)

    print(get_main_zones_by_category("房车"))
