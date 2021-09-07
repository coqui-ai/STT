#include "alphabet.h"
#include "ctcdecode/decoder_utils.h"

#include <fstream>

// std::getline, but handle newline conventions from multiple platforms instead
// of just the platform this code was built for
std::istream&
getline_crossplatform(std::istream& is, std::string& t)
{
  t.clear();

  // The characters in the stream are read one-by-one using a std::streambuf.
  // That is faster than reading them one-by-one using the std::istream.
  // Code that uses streambuf this way must be guarded by a sentry object.
  // The sentry object performs various tasks,
  // such as thread synchronization and updating the stream state.
  std::istream::sentry se(is, true);
  std::streambuf* sb = is.rdbuf();

  while (true) {
    int c = sb->sbumpc();
    switch (c) {
    case '\n':
      return is;
    case '\r':
      if(sb->sgetc() == '\n')
          sb->sbumpc();
      return is;
    case std::streambuf::traits_type::eof():
      // Also handle the case when the last line has no line ending
      if(t.empty())
        is.setstate(std::ios::eofbit);
      return is;
    default:
      t += (char)c;
    }
  }
}

int
Alphabet::init(const char *config_file)
{
  std::ifstream in(config_file, std::ios::in);
  if (!in) {
    return 1;
  }
  int index = 0;
  space_index_ = -2;
  for (std::string line; getline_crossplatform(in, line);) {
    if (line.size() == 2 && line[0] == '\\' && line[1] == '#') {
      line = '#';
    } else if (line[0] == '#') {
      continue;
    }
    //TODO: we should probably do something more i18n-aware here
    if (line == " ") {
      space_index_ = index;
    }
    if (line.length() == 0) {
      continue;
    }
    addEntry(line, index);
    ++index;
  }
  in.close();
  return 0;
}

void
Alphabet::InitFromLabels(const std::vector<std::string>& labels)
{
  space_index_ = -2;
  for (int idx = 0; idx < labels.size(); ++idx) {
    const std::string& label = labels[idx];
    if (label == " ") {
      space_index_ = idx;
    }
    addEntry(label, idx);
  }
}

std::string
Alphabet::SerializeText()
{
  std::stringstream out;

  out << "# Each line in this file represents the Unicode codepoint (UTF-8 encoded)\n"
      << "# associated with a numeric index.\n"
      << "# A line that starts with # is a comment. You can escape it with \\# if you wish\n"
      << "# to use '#' in the Alphabet.\n";

  for (int idx = 0; idx < entrySize(); ++idx) {
    out << getEntry(idx) << "\n";
  }

  out << "# The last (non-comment) line needs to end with a newline.\n";
  return out.str();
}

std::string
Alphabet::Serialize()
{
  // Should always be true in our usage, but this method will crash if for some
  // mystical reason it doesn't hold, so defensively assert it here.
  assert(isContiguous());

  // Serialization format is a sequence of (key, value) pairs, where key is
  // a uint16_t and value is a uint16_t length followed by `length` UTF-8
  // encoded bytes with the label.
  std::stringstream out;

  // We start by writing the number of pairs in the buffer as uint16_t.
  uint16_t size = entrySize();
  out.write(reinterpret_cast<char*>(&size), sizeof(size));

  for (int i = 0; i < GetSize(); ++i) {
    uint16_t key = i;
    string str = DecodeSingle(i);
    uint16_t len = str.length();
    // Then we write the key as uint16_t, followed by the length of the value
    // as uint16_t, followed by `length` bytes (the value itself).
    out.write(reinterpret_cast<char*>(&key), sizeof(key));
    out.write(reinterpret_cast<char*>(&len), sizeof(len));
    out.write(str.data(), len);
  }

  return out.str();
}

int
Alphabet::Deserialize(const char* buffer, const int buffer_size)
{
  // See util/text.py for an explanation of the serialization format.
  int offset = 0;
  if (buffer_size - offset < sizeof(uint16_t)) {
    return 1;
  }
  uint16_t size = *(uint16_t*)(buffer + offset);
  offset += sizeof(uint16_t);

  for (int i = 0; i < size; ++i) {
    if (buffer_size - offset < sizeof(uint16_t)) {
      return 1;
    }
    uint16_t label = *(uint16_t*)(buffer + offset);
    offset += sizeof(uint16_t);

    if (buffer_size - offset < sizeof(uint16_t)) {
      return 1;
    }
    uint16_t val_len = *(uint16_t*)(buffer + offset);
    offset += sizeof(uint16_t);

    if (buffer_size - offset < val_len) {
      return 1;
    }
    std::string val(buffer+offset, val_len);
    offset += val_len;

    addEntry(val, label);

    if (val == " ") {
      space_index_ = label;
    }
  }

  return 0;
}

size_t
Alphabet::GetSize() const
{
  return entrySize();
}

bool
Alphabet::CanEncodeSingle(const std::string& input) const
{
  return contains(input);
}

bool
Alphabet::CanEncode(const std::string& input) const
{
  for (auto cp : split_into_codepoints(input)) {
    if (!CanEncodeSingle(cp)) {
      return false;
    }
  }
  return true;
}

std::string
Alphabet::DecodeSingle(unsigned int label) const
{
  assert(label <= INT_MAX);
  return getEntry(label);
}

unsigned int
Alphabet::EncodeSingle(const std::string& string) const
{
  return getIndex(string);
}

std::string
Alphabet::Decode(const std::vector<unsigned int>& input) const
{
  std::string word;
  for (auto ind : input) {
    word += DecodeSingle(ind);
  }
  return word;
}

std::string
Alphabet::Decode(const unsigned int* input, int length) const
{
  std::string word;
  for (int i = 0; i < length; ++i) {
    word += DecodeSingle(input[i]);
  }
  return word;
}

std::vector<unsigned int>
Alphabet::Encode(const std::string& input) const
{
  std::vector<unsigned int> result;
  for (auto cp : split_into_codepoints(input)) {
    result.push_back(EncodeSingle(cp));
  }
  return result;
}

bool
UTF8Alphabet::CanEncodeSingle(const std::string& input) const
{
  return true;
}

bool
UTF8Alphabet::CanEncode(const std::string& input) const
{
  return true;
}

std::vector<unsigned int>
UTF8Alphabet::Encode(const std::string& input) const
{
  std::vector<unsigned int> result;
  for (auto byte_char : input) {
    std::string byte_str(1, byte_char);
    result.push_back(EncodeSingle(byte_str));
  }
  return result;
}
