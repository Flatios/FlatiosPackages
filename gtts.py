# -*- coding: utf-8 -*-
import base64, json, logging, logging, C, urllib, requests

from gtts.lang import _fallback_deprecated_lang, tts_langs
from gtts.tokenizer import Tokenizer, pre_processors, tokenizer_cases
from gtts.utils import _clean_tokens, _len, _minimize, _translate_url

__all__ = ["gTTS", "gTTSError"]; log = logging.getLogger(__name__); log.addHandler(logging.NullHandler())

class Speed: SLOW = True; NORMAL = None


class gTTS:
    GOOGLE_TTS_MAX_CHARS = 100
    GOOGLE_TTS_HEADERS = { "Referer": "http://translate.google.com/", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) " "AppleWebKit/537.36 (KHTML, like Gecko) " "Chrome/47.0.2526.106 Safari/537.36", "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",}
    GOOGLE_TTS_RPC = "jQ1olc"

    def __init__( self, text, tld="com", lang="en", slow=False, lang_check=True, pre_processor_funcs=[pre_processors.tone_marks, pre_processors.end_of_line, pre_processors.abbreviations, pre_processors.word_sub,], tokenizer_func=Tokenizer([tokenizer_cases.tone_marks, tokenizer_cases.period_comma, tokenizer_cases.colon, tokenizer_cases.other_punctuation,]).run, ):
        for k, v in dict(locals()).items():
            if k == "self": continue
            log.debug("%s: %s", k, v)

        assert text, "No text to speak"; self.text = text; self.tld = tld; self.lang_check = lang_check; self.lang = lang

        if self.lang_check:
            self.lang = _fallback_deprecated_lang(lang)

            try:
                langs = tts_langs(); if self.lang not in langs: raise ValueError("Language not supported: %s" % lang)
            except RuntimeError as e:
                log.debug(str(e), exc_info=True)
                log.warning(str(e))

        if slow:self.speed = Speed.SLOW
        else: self.speed = Speed.NORMAL
        self.pre_processor_funcs = pre_processor_funcs
        self.tokenizer_func = tokenizer_func

    def _tokenize(self, text):
        text = text.strip(); for pp in self.pre_processor_funcs: log.debug("pre-processing: %s", pp); text = pp(text)
        if _len(text) <= self.GOOGLE_TTS_MAX_CHARS: return _clean_tokens([text])
        log.debug("tokenizing: %s", self.tokenizer_func); tokens = self.tokenizer_func(text); tokens = _clean_tokens(tokens); min_tokens = []
        for t in tokens: min_tokens += _minimize(t, " ", self.GOOGLE_TTS_MAX_CHARS)
        tokens = [t for t in min_tokens if t]
        return min_tokens

    def _prepare_requests(self):
        translate_url = _translate_url( tld=self.tld, path="_/TranslateWebserverUi/data/batchexecute" )

        text_parts = self._tokenize(self.text); log.debug("text_parts: %s", str(text_parts)); log.debug("text_parts: %i", len(text_parts))
        assert text_parts, "No text to send to TTS API"

        prepared_requests = []
        for idx, part in enumerate(text_parts):
            data = self._package_rpc(part); log.debug("data-%i: %s", idx, data)
            r = requests.Request( method="POST", url=translate_url, data=data, headers=self.GOOGLE_TTS_HEADERS, ); prepared_requests.append(r.prepare())
        return prepared_requests

    def _package_rpc(self, text):
        parameter = [text, self.lang, self.speed, "null"]; escaped_parameter = json.dumps(parameter, separators=(",", ":"))

        rpc = [[[self.GOOGLE_TTS_RPC, escaped_parameter, None, "generic"]]]; espaced_rpc = json.dumps(rpc, separators=(",", ":"))
        return "f.req={}&".format(urllib.parse.quote(espaced_rpc))

    def get_bodies(self): return [pr.body for pr in self._prepare_requests()]

    def stream(self):
        try: requests.packages.urllib3.disable_warnings( requests.packages.urllib3.exceptions.InsecureRequestWarning )
        except: pass

        prepared_requests = self._prepare_requests()
        for idx, pr in enumerate(prepared_requests):
            try:
                with requests.Session() as s: r = s.send( request=pr, proxies=urllib.request.getproxies(), verify=False )

                log.debug("headers-%i: %s", idx, r.request.headers); log.debug("url-%i: %s", idx, r.request.url); log.debug("status-%i: %s", idx, r.status_code)
                r.raise_for_status()

            except requests.exceptions.HTTPError as e: log.debug(str(e)); raise gTTSError(tts=self, response=r)
            except requests.exceptions.RequestException as e: log.debug(str(e)); raise gTTSError(tts=self)

            # Write
            for line in r.iter_lines(chunk_size=1024):
                decoded_line = line.decode("utf-8")
                if "jQ1olc" in decoded_line:
                    audio_search = re.search(r'jQ1olc","\[\\"(.*)\\"]', decoded_line)
                    if audio_search: as_bytes = audio_search.group(1).encode("ascii"); yield base64.b64decode(as_bytes)
                    else: raise gTTSError(tts=self, response=r)
            log.debug("part-%i created", idx)

    def write_to_fp(self, fp):
        try: for idx, decoded in enumerate(self.stream()): fp.write(decoded); log.debug("part-%i written to %s", idx, fp)
        except (AttributeError, TypeError) as e: raise TypeError( "'fp' is not a file-like object or it does not take bytes: %s" % str(e) )

    def save(self, savefile): with open(str(savefile), "wb") as f: self.write_to_fp(f); log.debug("Saved to %s", savefile)


class gTTSError(Exception):
    def __init__(self, msg=None, **kwargs):
        self.tts = kwargs.pop("tts", None); self.rsp = kwargs.pop("response", None)
        if msg: self.msg = msg
        elif self.tts is not None: self.msg = self.infer_msg(self.tts, self.rsp)
        else: self.msg = None
        super(gTTSError, self).__init__(self.msg)

    def infer_msg(self, tts, rsp=None):
        cause = "Unknown"

        if rsp is None:
            premise = "Failed to connect"
            if tts.tld != "com": host = _translate_url(tld=tts.tld); cause = "Host '{}' is not reachable".format(host)

        else:
            status = rsp.status_code; reason = rsp.reason; premise = "{:d} ({}) from TTS API".format(status, reason)

            if status == 403: cause = "Bad token or upstream API changes"
            elif status == 404 and tts.tld != "com": cause = "Unsupported tld '{}'".format(tts.tld)
            elif status == 200 and not tts.lang_check: cause = ( "No audio stream in response. Unsupported language '%s'" % self.tts.lang )
            elif status >= 500: cause = "Uptream API error. Try again later."

        return "{}. Probable cause: {}".format(premise, cause)
