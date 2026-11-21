from raspimouse_python_driver.board import is_raspberry_pi4, read_model


def test_read_model_strips_trailing_nul(tmp_path):
    path = tmp_path / 'model'
    path.write_bytes(b'Raspberry Pi 4 Model B Rev 1.5\x00')
    assert read_model(path) == 'Raspberry Pi 4 Model B Rev 1.5'


def test_read_model_missing_file(tmp_path):
    assert read_model(tmp_path / 'missing') is None


def test_is_raspberry_pi4():
    assert is_raspberry_pi4('Raspberry Pi 4 Model B Rev 1.5')
    assert not is_raspberry_pi4('Raspberry Pi 5 Model B Rev 1.0')
    assert not is_raspberry_pi4('Raspberry Pi 3 Model B Plus Rev 1.3')
