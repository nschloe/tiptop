import tiptop


def test_braille_stream():
    stream = tiptop.BrailleStream(3, 0.0, 100.0)

    stream.add_value(10.0)
    assert stream.graph == "  ⢀"

    stream.add_value(30.0)
    assert stream.graph == "  ⣠"

    stream.add_value(60.0)
    assert stream.graph == " ⢀⣴"

    stream.add_value(90.0)
    assert stream.graph == " ⣠⣾"


def test_braille_stream():
    stream = tiptop.BrailleStreamTall(3, 4, 0.0, 100.0)

    stream.add_value(43.0)
    assert stream.graph == [
        "  ⢀",
        "  ⢀",
        "  ⢀",
    ]

    stream.add_value(30.0)
    assert stream.graph == "  ⣠"

    stream.add_value(60.0)
    assert stream.graph == " ⢀⣴"

    stream.add_value(90.0)
    assert stream.graph == " ⣠⣾"


def test_blockchar_stream():
    stream = tiptop.BlockCharStream(5, 0.0, 100.0)

    stream.add_value(10.0)
    assert stream.graph == "    ▁"

    stream.add_value(30.0)
    assert stream.graph == "   ▁▃"

    stream.add_value(60.0)
    assert stream.graph == "  ▁▃▅"

    stream.add_value(90.0)
    assert stream.graph == " ▁▃▅█"
