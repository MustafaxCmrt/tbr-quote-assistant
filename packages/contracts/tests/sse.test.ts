import assert from "node:assert/strict";
import test from "node:test";
import { createSseParser } from "../src/sse";

const bytes = (text: string) => new TextEncoder().encode(text);

test("utf8_multibyte_split", () => {
  const parser = createSseParser();
  const prefix = bytes('event: text_delta\ndata: {"text":"Ba');
  const source = bytes('event: text_delta\ndata: {"text":"Bağlantı çalışıyor ğüşiöç"}\n\n');
  assert.deepEqual(parser.push(source.slice(0, prefix.length + 1)), []);
  assert.deepEqual(parser.push(source.slice(prefix.length + 1)), [
    { event: "text_delta", data: '{"text":"Bağlantı çalışıyor ğüşiöç"}' },
  ]);
  assert.deepEqual(parser.finish(), []);
});

test("crlf_across_chunks", () => {
  const parser = createSseParser();
  assert.deepEqual(parser.push(bytes("event: done\r")), []);
  assert.deepEqual(parser.push(bytes('\ndata: {}\r')), []);
  assert.deepEqual(parser.push(bytes("\n\r")), [{ event: "done", data: "{}" }]);
  assert.deepEqual(parser.push(bytes("\n")), []);
});

test("multiple_events_in_one_chunk", () => {
  const parser = createSseParser();
  assert.deepEqual(parser.push(bytes("event: text_delta\ndata: bir\n\nevent: text_delta\ndata: iki\n\nevent: done\ndata: {}\n\n")), [
    { event: "text_delta", data: "bir" }, { event: "text_delta", data: "iki" }, { event: "done", data: "{}" },
  ]);
});

test("unfinished_final_event_is_discarded", () => {
  for (const ending of ['event: done\ndata: {', 'event: done\ndata: {}\n']) {
    const parser = createSseParser();
    assert.deepEqual(parser.push(bytes(`data: önce\n\n${ending}`)), [{ event: "message", data: "önce" }]);
    assert.deepEqual(parser.finish(), []);
    assert.deepEqual(parser.finish(), []);
    assert.throws(() => parser.push(bytes("\n")), /kapatıldı/);
  }
});

test("all_byte_boundaries_preserve_frames", () => {
  const source = bytes('event: text_delta\r\ndata: {"text":"Ğüşİöç"}\r\n\r\nevent: done\ndata: {}\n\n');
  for (let split = 0; split <= source.length; split++) {
    const parser = createSseParser();
    assert.deepEqual([...parser.push(source.slice(0, split)), ...parser.push(source.slice(split)), ...parser.finish()], [
      { event: "text_delta", data: '{"text":"Ğüşİöç"}' }, { event: "done", data: "{}" },
    ], `byte boundary ${split}`);
  }
});

test("comments_multiline_data_and_persistent_id", () => {
  const parser = createSseParser();
  assert.deepEqual(parser.push(bytes(": heartbeat\n\nid: 7\nevent: custom\ndata: bir\ndata:  iki\nretry: 1000\n\ndata:\n\nid: bad\0id\ndata: son\n\n")), [
    { event: "custom", id: "7", data: "bir\n iki" },
    { event: "message", id: "7", data: "" },
    { event: "message", id: "7", data: "son" },
  ]);
});

test("empty_stream_and_bare_cr", () => {
  const empty = createSseParser();
  assert.deepEqual(empty.push(new Uint8Array()), []);
  assert.deepEqual(empty.finish(), []);
  assert.deepEqual(createSseParser().push(bytes("data: a\r\rdata: b\r\r")), [
    { event: "message", data: "a" }, { event: "message", data: "b" },
  ]);
});

test("truncated_utf8_is_rejected", () => {
  const parser = createSseParser();
  assert.deepEqual(parser.push(new Uint8Array([0xc4])), []);
  assert.throws(() => parser.finish(), TypeError);
});
