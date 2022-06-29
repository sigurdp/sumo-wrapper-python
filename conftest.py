def pytest_addoption(parser):
    parser.addoption("--token", action="store", default="")

def pytest_generate_tests(metafunc):
    token = metafunc.config.getoption("token")

    print("test")
    print(token)

    if "token" in metafunc.fixturenames and token is not None:
        metafunc.parametrize("token", token)