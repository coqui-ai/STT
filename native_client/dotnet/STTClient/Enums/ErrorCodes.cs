namespace STTClient.Enums
{
    /// <summary>
    /// Error codes from the native Coqui STT binary.
    /// </summary>
    internal enum ErrorCodes
    {
        // OK
        STT_ERR_OK = 0x0000,

        // Missing invormations
        STT_ERR_NO_MODEL = 0x1000,

        // Invalid parameters
        STT_ERR_INVALID_ALPHABET = 0x2000,
        STT_ERR_INVALID_SHAPE = 0x2001,
        STT_ERR_INVALID_SCORER = 0x2002,
        STT_ERR_MODEL_INCOMPATIBLE = 0x2003,
        STT_ERR_SCORER_NOT_ENABLED = 0x2004,

        // Runtime failures
        STT_ERR_FAIL_INIT_MMAP = 0x3000,
        STT_ERR_FAIL_INIT_SESS = 0x3001,
        STT_ERR_FAIL_INTERPRETER = 0x3002,
        STT_ERR_FAIL_RUN_SESS = 0x3003,
        STT_ERR_FAIL_CREATE_STREAM = 0x3004,
        STT_ERR_FAIL_READ_PROTOBUF = 0x3005,
        STT_ERR_FAIL_CREATE_SESS = 0x3006,
        STT_ERR_FAIL_INSERT_HOTWORD = 0x3008,
        STT_ERR_FAIL_CLEAR_HOTWORD = 0x3009,
        STT_ERR_FAIL_ERASE_HOTWORD = 0x3010
    }
}
