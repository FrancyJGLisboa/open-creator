import sys
sys.path.append("..")
from creator.utils import stream_partial_json_to_dict


def test_stream_partial_json_to_dict():
    res = stream_partial_json_to_dict('{"language": "json", "code": "print(\'hello world')
    assert res == {"language": "json", "code": "print(\'hello world"}

def test_stream_partial_json_to_dict_empty_input():
    res = stream_partial_json_to_dict('')
    assert res == {}

def test_stream_partial_json_to_dict_invalid_json():
    try:
        res = stream_partial_json_to_dict('{"language": "json", "code": "print(\'hello world')
    except ValueError:
        assert True
    else:
        assert False

def test_stream_partial_json_to_dict_no_code_field():
    res = stream_partial_json_to_dict('{"language": "json"}')
    assert res == {"language": "json"}

def test_code_interpreter_parser():
    arguments = "{\n  \"language\": \"python\",\n  \"code\": \"\nimport json\n\ndef is_prime(n):\n    if n <= 1:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True\n\nprimes = []\nfor num in range(2, 201):\n    if is_prime(num):\n        primes.append(num)\n\nresult = {\n    'num_primes': len(primes),\n    'primes': primes\n}\n\njson_output = json.dumps(result)\njson_output\n\"\n}"
    for i in range(len(arguments)):
        json_str = arguments[:i+1]
        print(stream_partial_json_to_dict(json_str))

if __name__ == "__main__":
    test_code_interpreter_parser()
    
