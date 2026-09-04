export function parseSingleByteRange(rangeHeader, size) {
  if (!Number.isInteger(size) || size <= 0) {
    throw new RangeError("media size must be a positive integer");
  }

  if (rangeHeader === undefined || rangeHeader === null || rangeHeader === "") {
    return null;
  }

  if (typeof rangeHeader !== "string") {
    throw new RangeError("invalid byte range");
  }

  const match = /^bytes=([^,]+)$/.exec(rangeHeader.trim());
  if (!match) {
    throw new RangeError("only one byte range is supported");
  }

  const value = match[1].trim();
  const parts = value.split("-");
  if (parts.length !== 2) {
    throw new RangeError("invalid byte range");
  }

  const [rawStart, rawEnd] = parts;
  let start;
  let end;

  if (rawStart === "") {
    if (!/^\d+$/.test(rawEnd)) {
      throw new RangeError("invalid suffix byte range");
    }
    const suffixLength = Number(rawEnd);
    if (!Number.isSafeInteger(suffixLength) || suffixLength <= 0) {
      throw new RangeError("invalid suffix byte range");
    }
    start = Math.max(0, size - suffixLength);
    end = size - 1;
  } else {
    if (!/^\d+$/.test(rawStart) || (rawEnd !== "" && !/^\d+$/.test(rawEnd))) {
      throw new RangeError("invalid byte range");
    }
    start = Number(rawStart);
    end = rawEnd === "" ? size - 1 : Number(rawEnd);
    if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end)) {
      throw new RangeError("invalid byte range");
    }
    if (start >= size || end < start) {
      throw new RangeError("unsatisfiable byte range");
    }
    end = Math.min(end, size - 1);
  }

  return {
    start,
    end,
    length: end - start + 1,
  };
}
