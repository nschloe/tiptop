# https://stackoverflow.com/a/1094933/353337
def sizeof_fmt(num, suffix: str = "iB", sep=" ", fmt=".0f"):
    assert num >= 0
    for unit in ["B", "K", "M", "G", "T", "P", "E", "Z"]:
        # actually 1024, but be economical with the return string size:
        if unit != "B":
            unit += suffix

        if num < 1000:
            string = f"{{:{fmt}}}".format(num)
            return f"{string}{sep}{unit}"
        num /= 1024
    string = f"{{:{fmt}}}".format(num)
    return f"{string}{sep}Y{suffix}"


def val_to_color(val: float, minval: float, maxval: float) -> str:
    t = (val - minval) / (maxval - minval)
    k = round(t * 3)
    return {0: "color(4)", 1: "color(6)", 2: "color(6)", 3: "color(2)"}[k]
