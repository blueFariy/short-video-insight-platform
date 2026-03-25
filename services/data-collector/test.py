
def a(**kwargs):
    print([k for k in kwargs])

if __name__ == "__main__":
    # from app.tasks.hot_scan import scan_all_platforms
    #
    # scan_all_platforms()
    kwargs = {
        "a": 1,
        "b": 2
    }
    a(**kwargs)
