#ifndef LM_BUILD_CONFIG_H
#define LM_BUILD_CONFIG_H

#if defined _MSC_VER
    #define KENLM_EXPORT __declspec(dllexport)
#else
    #define KENLM_EXPORT __attribute__ ((visibility("default")))
#endif /* _MSC_VER */

#ifndef KENLM_MAX_ORDER
#define KENLM_MAX_ORDER 6
#endif /* KENLM_MAX_ORDER */

#endif /* LM_BUILD_CONFIG_H */
