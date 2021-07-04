#include <fstream>

#include "alphabet.h"
#include "ctcdecode/decoder_utils.h"
#include "cereal/types/unordered_map.hpp"
#include "cereal/archives/json.hpp"


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
  unsigned int label = 0;
  space_label_ = -2;
  for (std::string line; getline_crossplatform(in, line);) {
    if (line.size() == 2 && line[0] == '\\' && line[1] == '#') {
      line = '#';
    } else if (line[0] == '#') {
      continue;
    }
    //TODO: we should probably do something more i18n-aware here
    if (line == " ") {
      space_label_ = label;
    }
    if (line.length() == 0) {
      continue;
    }
    label_to_str_[label] = line;
    str_to_label_[line] = label;
    ++label;
  }
  size_ = label;
  in.close();
  return 0;
}

std::string
Alphabet::Serialize()
{
  std::stringstream out;
  {
    cereal::JSONOutputArchive arc(out, cereal::JSONOutputArchive::Options::NoIndent());
    arc(size_, label_to_str_);
  }

  return out.str();
}

int
Alphabet::Deserialize(const char* buffer, const int buffer_size)
{
  std::string input(buffer, buffer_size);
  std::stringstream stream(input);
  cereal::JSONInputArchive arc(stream);
  arc(size_, label_to_str_);

  for (auto it : label_to_str_) {
    str_to_label_[it.second] = it.first;
    if (it.second == " ") {
      space_label_ = it.first;
    }
  }

  return 0;
}

bool
Alphabet::CanEncodeSingle(const std::string& input) const
{
  auto it = str_to_label_.find(input);
  return it != str_to_label_.end();
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
  auto it = label_to_str_.find(label);
  if (it != label_to_str_.end()) {
    return it->second;
  } else {
    std::cerr << "Invalid label " << label << std::endl;
    abort();
  }
}

unsigned int
Alphabet::EncodeSingle(const std::string& string) const
{
  auto it = str_to_label_.find(string);
  if (it != str_to_label_.end()) {
    return it->second;
  } else {
    std::cerr << "Invalid string " << string << std::endl;
    abort();
  }
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
