#include <unistd.h>
#include <sys/types.h>
#include <sys/errno.h>
#include <machine/sysnews.h>
#include <machine/machid.h>

extern int errno; /* Error codes from standard library */

void handle_machid()
{
    struct machid newsMachineId;
    if(!sysnews(NEWS_MACHID, &newsMachineId))
    {
        printf("NEWS Machine ID\n");
        printf("  Model name: %d\n", newsMachineId.m_pwb);
        printf("  Model code: %d\n", newsMachineId.m_model);
        printf("  Serial number: %d\n", newsMachineId.m_serial);
        printf("  Reserved[0]: %d\n", newsMachineId.m_reserve0);
        printf("  Reserved[1]: %d\n", newsMachineId.m_reserve1);
    }
    else
    {
        printf("Unable to get machine ID! Error code %d\n", errno);
    }
}

void handle_machtype()
{
    struct machtype newsMachineType;
    if(!sysnews(NEWS_MACHTYPE, &newsMachineType))
    {
        printf("NEWS Machine Type Data\n");
        printf("  Model name = %s\n", newsMachineType.mt_model);
        printf("  Machine name = %s\n", newsMachineType.mt_machine);
        printf("  CPU = %s\n", newsMachineType.mt_maincpu);
        printf("  I/O Processor = %s\n", newsMachineType.mt_subcpu);
        printf("  Floating point Processor = %s\n", newsMachineType.mt_fpa);
        printf("  Data cache size = %d\n", newsMachineType.mt_dcache);
        printf("  Instruction cache size = %d\n", newsMachineType.mt_icache);
        printf("  Cache control data = %d\n", newsMachineType.mt_cachectrl);
        printf("  Reserved = %d\n", newsMachineType.mt_reserved);
    }
    else
    {
        printf("Unable to get machine type! Error code %d\n", errno);
    }
}

void handle_machparam()
{
    struct machparam mp;
    if(!sysnews(NEWS_MACHPARAM, &mp))
    {
        printf("NEWS Machine Parameters\n");
        printf("  Physical memory size = %d\n", mp.mp_physmem);
        printf("  Avaliable mem = %d\n", mp.mp_maxmem);
        printf("  Max users = %d\n", mp.mp_maxusers);
        printf("  CPU speed = %d\n", mp.mp_cpuspeed);
        printf("  Boot device = %d\n", mp.mp_bootdev);
        printf("  Boot switch settings = %d\n", mp.mp_bootsw);
        printf("  Reserved[1] = %d\n", mp.mp_reserved1);
        printf("  Reserved[2] = %d\n", mp.mp_reserved2);
    }
    else
    {
        printf("Unable to get machine parameters! Error code %d\n", errno);
    }
}

void handle_os_version()
{
    int bufferSize = 200;
    char *version;
    version = (char *)malloc(bufferSize);
    if(sysnews(NEWS_VERSION, version, bufferSize) == -1)
    {
        if(errno == 2)
        {
            printf("Buffer too small! Truncated OS version: %s\n", version);
        }
        else
        {
            printf("Unable to get OS version! Error code %d\n", errno);
        }
    }
    else
    {
        printf("Active NEWS-OS Version: %s\n", version);
    }
    free(version);
}

void handle_sysctld()
{
    int sysctld;
    if(!sysnews(NEWS_GETSYSDINFO, &sysctld))
    {
        printf("Sysctld info: %d\n", sysctld);
    }
    else
    {
        printf("Unable to get sysctld status! Error code %d\n", errno);
    }
}

int main(int argc, char *argv[])
{
    handle_os_version();
    handle_machid();
    handle_machtype();
    handle_machparam();
    handle_sysctld();

    return 0;
}
