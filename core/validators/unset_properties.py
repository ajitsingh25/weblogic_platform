
def run(config):
    result = True
    enum = config.keys()
    while enum.hasMoreElements():
        key = enum.nextElement()
        if config.getProperty(key) == "?":
            log.error("Property not set: " + key)
            result = False
    return result
